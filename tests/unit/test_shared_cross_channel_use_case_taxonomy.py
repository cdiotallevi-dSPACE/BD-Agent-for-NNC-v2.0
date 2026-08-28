from bd_agent_neural_net_coder.evidence_context import analyze_patent
from bd_agent_neural_net_coder.nnc_scoring import score_patent_use_case
from bd_agent_neural_net_coder.patent_native_discovery import patent_result_quality, rank_patent
from bd_agent_neural_net_coder.search_orchestrator import candidate_retrieval_priority, generate_queries
from bd_agent_neural_net_coder.shared_use_case_taxonomy import all_matching_terms, match_use_case_families


ASSIGNEES = ["Stellantis Auto SAS", "FCA US LLC", "PSA Automobiles SA"]


PATENT_ORACLES = [
    ("US12091027B2", "Vehicle electric motor temperature estimation using neural network model",
     "electric_machine_thermal_state_estimation"),
    ("US20260110742A1", "Transfer learning based battery state of power estimation techniques with updating through battery lifetime",
     "battery_power_capability_and_adaptation"),
    ("US10788396B2", "Using an artificial neural network for combustion phasing control in a spark ignited internal combustion engine",
     "combustion_and_powertrain_neural_control"),
    ("US11594040B2", "Multiple resolution deep neural networks for vehicle autonomous driving systems",
     "autonomous_driving_neural_perception"),
]


def _record(publication_number, title):
    return {
        "source_provider": "uspto_patent_file_wrapper",
        "source_record_id": publication_number,
        "patent_url": f"https://data.uspto.gov/patent-file-wrapper/search/details/{publication_number}/application-data",
        "publication_number": publication_number,
        "title": title,
        "abstract": "A vehicle controller accesses and executes a trained neural network model in real time.",
        "current_assignees": ["FCA US LLC"], "original_assignees": ["FCA US LLC"],
        "classifications": {"cpc": ["G06N3/02"], "ipc": []},
        "patent_native_enumeration_or_search": True,
    }


def test_four_stellantis_oracles_rank_from_generic_taxonomy_without_seed_urls():
    terms = all_matching_terms()
    for publication_number, title, expected_family in PATENT_ORACLES:
        record = _record(publication_number, title)
        quality = patent_result_quality(record, ASSIGNEES, terms)
        ranked = rank_patent(record, ASSIGNEES)
        assert quality["status"] == "usable"
        assert quality["taxonomy_signal"] is True
        assert expected_family in ranked["matched_use_case_families"]
        assert ranked["local_rank_score"] >= 80


def test_shared_terms_prioritize_web_and_pdf_candidates_not_only_patents():
    profile = {"company_name": "Example Motors", "company_aliases": ["Example"],
               "official_domains": ["example.com"]}
    web = {"title_hint": "Neural motor temperature estimation", "snippet": "real-time vehicle controller",
           "canonical_url": "https://example.com/research/motor-temperature", "source_domain_class": "official_company"}
    pdf = {"title_hint": "Battery state of power estimation", "snippet": "transfer learning battery model",
           "canonical_url": "https://publisher.example/paper.pdf", "source_domain_class": "third_party_analytics"}
    web_score, web_reasons = candidate_retrieval_priority(web, profile)
    pdf_score, pdf_reasons = candidate_retrieval_priority(pdf, profile)
    assert web_score > 100 and "high_priority_use_case_in_title" in web_reasons
    assert pdf_score > 0 and "high_priority_use_case_in_title" in pdf_reasons


def test_query_templates_are_generic_cross_channel_and_cover_every_assignee():
    profile = {"company_name": "Example Motors", "company_aliases": ["Example"],
               "official_domains": ["example.com"], "official_asset_domains": [],
               "related_corporate_domains": [], "partner_domains": [], "specialist_domains": [],
               "publication_hubs": [], "company_research_affiliations": [], "industry": "automotive",
               "validated_source_assignees": [{"assignee_name": name} for name in ASSIGNEES]}
    queries = generate_queries(profile, "fast_iteration")
    rendered = [query.rendered_query for query in queries]
    assert any('site:example.com "motor temperature estimation"' in query for query in rendered)
    assert any('"motor thermal management" filetype:pdf' in query and '"Example"' in query for query in rendered)
    for assignee in ASSIGNEES:
        assert any(f'"{assignee}"' in query and '"motor thermal management"' in query
                   and 'filetype:pdf' not in query for query in rendered)
        assert any(f'"{assignee}"' in query and '"motor thermal management" filetype:pdf' in query
                   for query in rendered)
        assert any(f'"{assignee}" "neural network"' in query for query in rendered)
        assert any(f'"{assignee}" "transfer learning"' in query for query in rendered)


def test_public_oem_application_vocabulary_is_complete_and_locally_matchable():
    required = {
        "battery state estimation", "motor thermal management", "vehicle perception",
        "driver monitoring", "predictive diagnostics", "software-defined vehicle",
        "intelligent battery management", "sensorless estimation", "AI-enabled vehicle control",
    }
    assert required.issubset(set(all_matching_terms()))
    matches = match_use_case_families("An AI-enabled vehicle control system uses sensorless estimation.")
    assert "indirect_physical_state_and_virtual_sensing" in matches


def test_application_only_queries_do_not_require_ai_vocabulary():
    profile = {"company_name": "Example Motors", "company_aliases": ["Example"],
               "official_domains": ["example.com"], "official_asset_domains": [],
               "related_corporate_domains": [], "partner_domains": [], "specialist_domains": [],
               "publication_hubs": [], "company_research_affiliations": [], "industry": "automotive",
               "validated_source_assignees": []}
    queries = generate_queries(profile, "fast_iteration")
    rendered = {query.rendered_query for query in queries}
    assert 'site:example.com "battery state estimation"' in rendered
    assert 'site:example.com "driver monitoring"' in rendered
    assert 'site:example.com "software-defined vehicle"' in rendered


def test_full_text_assessment_and_scoring_use_the_same_family_vocabulary():
    text = ("FCA US LLC uses a trained artificial neural network in a vehicle controller for real-time "
            "rotor temperature estimation and motor control.")
    matches = match_use_case_families(text)
    analysis = analyze_patent(text)
    scoring = score_patent_use_case(analysis, text)
    assert "electric_machine_thermal_state_estimation" in matches
    assert "electric_machine_thermal_state_estimation" in analysis["use_case_classes"]
    assert scoring["use_case_score"] >= 50


def test_motor_temperature_virtual_sensor_is_strongest_fixed_inference_pilot():
    text = ("A controller of the vehicle accesses a trained artificial neural network temperature estimation model. "
            "The recurrent-type ANN uses phase current, motor speed and coolant temperature to estimate stator and "
            "rotor temperatures in real-time. The model is stored by the controller. Temperature sensors are only "
            "used temporarily for training and are not required for vehicle implementation.")
    analysis = analyze_patent(text)
    scoring = score_patent_use_case(analysis, text)
    assert analysis["model_architecture"]["recurrent_ann"] == "confirmed"
    assert analysis["runtime_and_lifecycle"]["fixed_trained_inference"] == "confirmed"
    assert analysis["runtime_and_lifecycle"]["sensor_elimination_or_training_only_sensor"] == "confirmed"
    assert analysis["pilot_assessment"]["priority_class"] == "strongest_first_pilot"
    assert scoring["use_case_score"] >= 65


def test_lstm_sop_separates_fixed_inference_from_transfer_learning_update():
    text = ("The control system of the electrified vehicle performs an LSTM battery voltage estimation model and "
            "binary search for real-time battery state of power estimation. The model has two hidden LSTM layers, "
            "each with 16 hidden units. The controller is configured to utilize the trained model. A separate low "
            "learning rate transfer learning process updates the model over battery lifetime.")
    analysis = analyze_patent(text)
    scoring = score_patent_use_case(analysis, text)
    assert analysis["model_architecture"]["lstm"] == "confirmed"
    assert analysis["model_architecture"]["hidden_layer_count"] == 2
    assert analysis["model_architecture"]["hidden_units_or_neurons_per_layer"] == 16
    assert analysis["nnc_scope_boundary"]["fixed_trained_inference_fit"] == "high"
    assert analysis["nnc_scope_boundary"]["online_transfer_learning_handling"] == "separate_qualification_required"
    assert analysis["pilot_assessment"]["priority_class"] == "strong_pilot_separate_online_learning"
    assert scoring["use_case_score"] >= 65


def test_compact_combustion_ann_keeps_technical_fit_separate_from_recency():
    text = ("A trained feed-forward artificial neural network controls combustion phasing. The generated ANN "
            "calibration is stored by the engine controller and implemented by the controller for spark timing. "
            "Four inputs include air charge, engine speed, intake and exhaust camshaft positions. Two hidden layers "
            "have twelve neurons per layer and produce base and MBT spark timing.")
    analysis = analyze_patent(text)
    scoring = score_patent_use_case(analysis, text)
    assert analysis["model_architecture"]["feed_forward_ann"] == "confirmed"
    assert analysis["model_architecture"]["hidden_units_or_neurons_per_layer"] == 12
    assert analysis["pilot_assessment"]["priority_class"] == "strong_compact_embedded_pilot_legacy_ice_context"
    assert analysis["pilot_assessment"]["technical_fit_penalized_for_age"] is False
    assert analysis["pilot_assessment"]["commercial_recency_qualification"] == "required"
    assert scoring["use_case_score"] >= 65
