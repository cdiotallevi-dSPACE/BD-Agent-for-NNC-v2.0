from __future__ import annotations
import hashlib, json, math, os, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import chromadb
import pymupdf as fitz
import httpx
from contextvars import ContextVar
from functools import wraps
from .config_manager import load_yaml
from .core import atomic_json
from .model_runtime import EMBEDDING_MODEL, validate_models

COLLECTION_NAME="nnc_portfolio_documents"
DIMENSION=1024
SCHEMA_VERSION="1.0.0"
PARSER_VERSION="1.0.0"
CHUNKER_VERSION="1.0.0"
_session = ContextVar("bda_portfolio_session", default=None)


def portfolio_scope(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if _session.get() is not None:
            return fn(*args, **kwargs)
        with httpx.Client() as client:
            token = _session.set({"http": client, "stores": {}, "validated": {}, "signatures": {}, "vectors": {}})
            try:
                result = fn(*args, **kwargs)
                for root in _session.get()["signatures"]:
                    _check_generation(Path(root))
                return result
            finally:
                _session.reset(token)
    return wrapped


def _check_generation(root):
    session = _session.get()
    if session is None:
        return
    runtime = root / "data/dspace_portfolio_runtime"
    if (runtime / "locks/ingestion.lock").exists():
        raise RuntimeError("portfolio_index_changed_during_run: ingestion active")
    signature = tuple(((runtime / name).stat().st_mtime_ns, (runtime / name).stat().st_size)
                      for name in ("collection_manifest.json", "document_manifest.json"))
    key = str(root.resolve())
    previous = session["signatures"].setdefault(key, signature)
    if previous != signature:
        raise RuntimeError("portfolio_index_changed_during_run")


def _store(root):
    session = _session.get()
    if session is None:
        return ChromaPortfolioStore(root / "data/dspace_portfolio_runtime/chroma_db")
    key = str(root.resolve())
    if key not in session["stores"]:
        session["stores"][key] = ChromaPortfolioStore(root / "data/dspace_portfolio_runtime/chroma_db")
    return session["stores"][key]


def local_model_post(*args, **kwargs):
    session = _session.get()
    return (session["http"].post if session is not None else httpx.post)(*args, **kwargs)


def prefetch_portfolio(root, queries, batch_size=8):
    """Bounded embedding requests; scoring/Chroma queries still run in order.

    A failed batch falls back to the existing per-query retry path. Cache is
    private to one company run, never reused across model/index versions.
    """
    session = _session.get()
    if session is None or not queries:
        return
    _check_generation(root)
    unique = list(dict.fromkeys(queries))
    embedder = OllamaEmbeddingClient(client=session["http"])
    for start in range(0, len(unique), max(1, batch_size)):
        batch = unique[start:start + max(1, batch_size)]
        try:
            vectors = embedder.embed(batch)
        except RuntimeError:
            # Do not make a batch-level failure suppress otherwise good queries.
            continue
        session["vectors"].update(zip(batch, vectors))
    _check_generation(root)

def now() -> str: return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return "sha256:"+h.hexdigest()
def normalize(value: str) -> str: return re.sub(r"[^a-z0-9]+"," ",value.lower()).strip()

class OllamaEmbeddingClient:
    def __init__(self, url="http://127.0.0.1:11434", model=EMBEDDING_MODEL, client=None): self.url=url; self.model=model; self.http=client
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts: return []
        last=None
        for attempt in range(3):
            try:
                r=(self.http.post if self.http is not None else httpx.post)(self.url+"/api/embed",json={"model":self.model,"input":texts},timeout=120); r.raise_for_status()
                vectors=r.json().get("embeddings",[])
                if len(vectors)!=len(texts): raise ValueError("embedding count mismatch")
                for vector in vectors:
                    if len(vector)!=DIMENSION or not vector or any(not math.isfinite(x) for x in vector): raise ValueError("invalid embedding vector")
                return vectors
            except Exception as exc:
                last=exc
                if attempt<2: time.sleep(1.5*(attempt+1))
        raise RuntimeError(f"bge-large embedding failed: {last}") from last

class ChromaPortfolioStore:
    def __init__(self,path: Path):
        self.path=path; path.mkdir(parents=True,exist_ok=True)
        self.client=chromadb.PersistentClient(path=str(path))
        self.collection=self.client.get_or_create_collection(COLLECTION_NAME,metadata={"hnsw:space":"cosine","embedding_model":EMBEDDING_MODEL,"embedding_dimension":DIMENSION,"schema_version":SCHEMA_VERSION,"chunker_version":CHUNKER_VERSION})
    def upsert_chunks(self,chunks,embeddings):
        self.collection.upsert(ids=[c["chunk_id"] for c in chunks],documents=[c["text"] for c in chunks],metadatas=[{k:v for k,v in c.items() if k not in ("text","chunk_id")} for c in chunks],embeddings=embeddings)
    def delete_document_chunks(self,source_hash): self.collection.delete(where={"source_hash":{"$eq":source_hash}})
    def delete_chunk_ids(self,ids): 
        if ids:self.collection.delete(ids=ids)
    def query(self,embedding,portfolio_item_id,top_k):
        return self.collection.query(query_embeddings=[embedding],where={"dspace_portfolio_item_id":{"$eq":portfolio_item_id}},n_results=top_k,include=["documents","metadatas","distances"])
    def count(self): return self.collection.count()
    def get(self,ids): return self.collection.get(ids=ids,include=["documents","metadatas"])
    def reset(self):
        try:self.client.delete_collection(COLLECTION_NAME)
        except Exception:pass
        self.collection=self.client.create_collection(COLLECTION_NAME,metadata={"hnsw:space":"cosine","embedding_model":EMBEDDING_MODEL,"embedding_dimension":DIMENSION,"schema_version":SCHEMA_VERSION,"chunker_version":CHUNKER_VERSION})
    def validate_collection_metadata(self):
        meta=self.collection.metadata or {}
        return meta.get("embedding_model")==EMBEDDING_MODEL and int(meta.get("embedding_dimension",0))==DIMENSION and meta.get("hnsw:space")=="cosine"

def resolve_item(filename: str,config_root: Path) -> tuple[str,str]:
    profiles=load_yaml(config_root/"dspace_portfolio/dspace_portfolio_profiles.yaml")["dspace_portfolio_items"]
    aliases=load_yaml(config_root/"dspace_portfolio/dspace_portfolio_aliases.yaml")["aliases"]
    hay=normalize(Path(filename).stem)
    priority=(("neural net coder","neural_net_coder"),("nnc","neural_net_coder"))
    padded=f" {hay} "
    for needle,resolved in priority:
        if f" {needle} " in padded:
            name=next(p["name"] for p in profiles if p["dspace_portfolio_item_id"]==resolved)
            return resolved,name
    candidates=set()
    for alias,item in aliases.items():
        if normalize(alias) in hay:candidates.add(item)
    for p in profiles:
        if normalize(p["name"]) in hay or normalize(p["dspace_portfolio_item_id"]) in hay:candidates.add(p["dspace_portfolio_item_id"])
    # Prefer the longest matching alias when generic and specific aliases overlap.
    matches=[(len(normalize(a)),item) for a,item in aliases.items() if normalize(a) in hay]
    if matches:
        longest=max(n for n,_ in matches); candidates={item for n,item in matches if n==longest}
    if len(candidates)!=1: raise ValueError(f"portfolio-item mapping {'ambiguous' if candidates else 'missing'}: {filename} -> {sorted(candidates)}")
    item=next(iter(candidates)); name=next(p["name"] for p in profiles if p["dspace_portfolio_item_id"]==item)
    return item,name

def parse_pdf(path: Path) -> tuple[list[dict],dict]:
    doc=fitz.open(path); pages=[]; warnings=[]
    for number,page in enumerate(doc,1):
        blocks=sorted(page.get_text("blocks"),key=lambda b:(round(b[1],1),b[0]))
        text="\n".join(re.sub(r"\s+"," ",b[4]).strip() for b in blocks if b[4].strip())
        if len(text)<40:warnings.append(f"page_{number}_low_text")
        pages.append({"page":number,"text":text})
    meta={"page_count":len(doc),"metadata":dict(doc.metadata or {}),"warnings":warnings}; doc.close()
    if not any(len(p["text"])>=40 for p in pages): raise ValueError("ocr_required: no usable PDF text")
    return pages,meta

def detect_section(text: str) -> str:
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    for line in lines[:8]:
        if 3<=len(line)<=100 and (line.isupper() or len(line.split())<=10): return line[:150]
    return "Document content"

def chunk_pages(pages,item_id,item_name,filename,source_hash):
    chunks=[]; seq=0
    for page in pages:
        words=page["text"].split()
        if not words: continue
        section=detect_section(page["text"])
        start=0
        while start<len(words):
            end=min(len(words),start+450)
            if len(words)-end<250:end=len(words)
            selected=words[start:end]
            if len(selected)<40:break
            seq+=1; chunk_id=f"{item_id}__{source_hash[7:19]}__p{page['page']}-{page['page']}__c{seq:04d}"
            text=" ".join(selected)
            lowered=text.lower()
            chunk_type="capability" if any(x in lowered for x in ("simulation","test","hil","fpga","capability","control")) else "overview"
            chunks.append({"chunk_id":chunk_id,"text":text,"dspace_portfolio_item_id":item_id,"dspace_portfolio_item_name":item_name,"source_filename":filename,"source_hash":source_hash,"page_start":page["page"],"page_end":page["page"],"section":section,"chunk_type":chunk_type,"parser_version":PARSER_VERSION,"chunker_version":CHUNKER_VERSION,"embedding_model":EMBEDDING_MODEL})
            if end==len(words):break
            start=max(end-54,start+1)
    return chunks

def ingest(root: Path,source: Path|None=None,rebuild=False) -> dict:
    source=source or root/"data/dspace_portfolio_documents"; runtime=root/"data/dspace_portfolio_runtime"
    if not source.exists(): raise FileNotFoundError(source)
    pdfs=sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower()==".pdf")
    if not pdfs: raise ValueError("no PDFs discovered")
    model=validate_models()
    if not model["semantic_runtime_ready"]: raise RuntimeError("bge-large model preflight failed")
    runtime.mkdir(parents=True,exist_ok=True); locks=runtime/"locks"; locks.mkdir(exist_ok=True); lock=locks/"ingestion.lock"
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise RuntimeError("portfolio ingestion writer lock already exists")
    try:
        old_path=runtime/"document_manifest.json"
        old=json.loads(old_path.read_text(encoding="utf-8")).get("documents",[]) if old_path.exists() else []
        old_by_name={d["filename"]:d for d in old if d.get("status")=="active"}
        store=ChromaPortfolioStore(runtime/"chroma_db")
        if rebuild: store.reset(); old_by_name={}
        embedder=OllamaEmbeddingClient(); records=[]; counters={"discovered":len(pdfs),"unchanged":0,"added":0,"updated":0,"removed":0,"failed":0,"ocr_required":0,"duplicates":0,"chunks_created":0,"chunks_reused":0,"chunks_deleted":0,"chunks_embedded":0}
        seen=set(); seen_hashes={}
        for pdf in pdfs:
            seen.add(pdf.name); digest=file_hash(pdf); previous=old_by_name.get(pdf.name)
            if digest in seen_hashes:
                counters["duplicates"]+=1
                records.append({"filename":pdf.name,"source_hash":digest,"status":"duplicate","duplicate_of":seen_hashes[digest],"latest_ingested_at":now()})
                continue
            seen_hashes[digest]=pdf.name
            if previous and previous.get("source_hash")==digest:
                records.append(previous); counters["unchanged"]+=1; counters["chunks_reused"]+=previous.get("chunk_count",0); continue
            try:
                item,name=resolve_item(pdf.name,root/"config"); pages,parsed=parse_pdf(pdf); chunks=chunk_pages(pages,item,name,pdf.name,digest)
                if not chunks: raise ValueError("no chunks generated")
                embeddings=[]
                for i in range(0,len(chunks),16): embeddings.extend(embedder.embed([c["text"] for c in chunks[i:i+16]]))
                if previous:
                    store.delete_chunk_ids(previous.get("indexed_chunk_ids",[])); counters["updated"]+=1; counters["chunks_deleted"]+=previous.get("chunk_count",0)
                else:counters["added"]+=1
                store.upsert_chunks(chunks,embeddings); counters["chunks_created"]+=len(chunks); counters["chunks_embedded"]+=len(chunks)
                records.append({"dspace_portfolio_item_id":item,"dspace_portfolio_item_name":name,"filename":pdf.name,"source_hash":digest,"parser_status":"parsed","page_count":parsed["page_count"],"chunk_count":len(chunks),"indexed_chunk_ids":[c["chunk_id"] for c in chunks],"first_ingested_at":previous.get("first_ingested_at") if previous else now(),"latest_ingested_at":now(),"status":"active","warnings":parsed["warnings"]})
            except Exception as exc:
                if "ocr_required" in str(exc):
                    counters["ocr_required"]+=1
                    records.append({"filename":pdf.name,"source_hash":digest,"parser_status":"ocr_required","status":"ocr_required","error":str(exc),"latest_ingested_at":now()})
                else:
                    counters["failed"]+=1
                    if previous: records.append(previous|{"update_error":str(exc)})
                    else: records.append({"filename":pdf.name,"source_hash":digest,"status":"failed","error":str(exc),"latest_ingested_at":now()})
        for filename,previous in old_by_name.items():
            if filename not in seen:
                store.delete_chunk_ids(previous.get("indexed_chunk_ids",[])); counters["removed"]+=1; counters["chunks_deleted"]+=previous.get("chunk_count",0)
                records.append(previous|{"status":"stale","latest_ingested_at":now()})
        if counters["failed"]: raise RuntimeError(f"{counters['failed']} portfolio PDFs failed ingestion")
        active=[r for r in records if r.get("status")=="active"]; created=now()
        collection_manifest={"collection_name":COLLECTION_NAME,"persistent_path":"data/dspace_portfolio_runtime/chroma_db","embedding_provider":"ollama","embedding_model":EMBEDDING_MODEL,"embedding_model_digest":model["embedding"]["digest"],"embedding_dimension":DIMENSION,"distance_metric":"cosine","document_count":len(active),"chunk_count":store.count(),"created_at":created,"updated_at":created,"status":"ready","schema_version":SCHEMA_VERSION,"chunker_version":CHUNKER_VERSION}
        atomic_json(runtime/"document_manifest.json",{"documents":records}); atomic_json(runtime/"collection_manifest.json",collection_manifest)
        report={"status":"completed","mode":"rebuild" if rebuild else "incremental","counters":counters,"collection":collection_manifest,"document_manifest_path":str(runtime/"document_manifest.json"),"collection_manifest_path":str(runtime/"collection_manifest.json")}
        atomic_json(runtime/"ingestion_report.json",report)
        validation=validate_index(root)
        if not validation["ready"]: raise RuntimeError(f"post-ingestion validation failed: {validation}")
        return report
    finally:
        try:os.close(fd)
        except Exception:pass
        if lock.exists():lock.unlink()

def validate_index(root: Path) -> dict:
    session = _session.get()
    key = str(root.resolve())
    if session is not None and key in session["validated"]:
        _check_generation(root)
        return session["validated"][key]
    runtime=root/"data/dspace_portfolio_runtime"; mp=runtime/"collection_manifest.json"; dp=runtime/"document_manifest.json"; chroma=runtime/"chroma_db"
    errors=[]
    if not (mp.exists() and dp.exists() and chroma.exists()): return {"ready":False,"status":"failed_portfolio_index_preflight","errors":["runtime artifacts missing"]}
    manifest=json.loads(mp.read_text(encoding="utf-8")); documents=json.loads(dp.read_text(encoding="utf-8")).get("documents",[])
    if manifest.get("embedding_model")!=EMBEDDING_MODEL:errors.append("embedding model mismatch")
    if manifest.get("embedding_dimension")!=DIMENSION:errors.append("embedding dimension mismatch")
    try:
        _check_generation(root)
        store=_store(root)
        if not store.validate_collection_metadata():errors.append("collection metadata invalid")
        if store.count()<=0 or store.count()!=manifest.get("chunk_count"):errors.append("collection count invalid")
        active=[d for d in documents if d.get("status")=="active"]
        if not active:errors.append("no active documents")
        ids=[x for d in active for x in d.get("indexed_chunk_ids",[])]
        if len(ids)!=len(set(ids)):errors.append("duplicate chunk IDs")
        if ids and len(store.get(ids[:min(5,len(ids))])["ids"])==0:errors.append("sample chunks not retrievable")
    except Exception as exc:errors.append(str(exc))
    result={"ready":not errors,"status":"ready" if not errors else "failed_portfolio_index_preflight","errors":errors,"collection_count":manifest.get("chunk_count",0),"document_count":manifest.get("document_count",0),"embedding_model":manifest.get("embedding_model"),"embedding_dimension":manifest.get("embedding_dimension")}
    if session is not None and result["ready"]:
        session["validated"][key] = result
    return result

def retrieve(root: Path,query: str,item_id: str,top_k=8) -> dict:
    pre=validate_index(root)
    if not pre["ready"]:raise RuntimeError("failed_portfolio_index_preflight")
    store=_store(root)
    session=_session.get()
    vector=session["vectors"].get(query) if session is not None else None
    if vector is None:
        vector=OllamaEmbeddingClient(client=session["http"] if session is not None else None).embed([query])[0]
    result=store.query(vector,item_id,top_k)
    _check_generation(root)
    candidates=[]
    ids=result.get("ids",[[]])[0]; docs=result.get("documents",[[]])[0]; metas=result.get("metadatas",[[]])[0]; distances=result.get("distances",[[]])[0]
    page_counts={}; section_counts={}
    for cid,text,meta,distance in zip(ids,docs,metas,distances):
        similarity=1.0-float(distance); selected=similarity>=0.35 and page_counts.get(meta["page_start"],0)<2 and section_counts.get(meta["section"],0)<3 and meta.get("chunk_type")!="overview"
        if selected:page_counts[meta["page_start"]]=page_counts.get(meta["page_start"],0)+1; section_counts[meta["section"]]=section_counts.get(meta["section"],0)+1
        candidates.append({"chunk_id":cid,"source_filename":meta["source_filename"],"page_start":meta["page_start"],"page_end":meta["page_end"],"section":meta["section"],"chunk_type":meta["chunk_type"],"distance":float(distance),"similarity":similarity,"selected":selected,"text_preview":text[:300]})
    return {"dspace_portfolio_item_id":item_id,"query_text":query,"embedding_model":EMBEDDING_MODEL,"collection_name":COLLECTION_NAME,"top_k":top_k,"minimum_similarity":0.35,"returned_chunks":candidates}
