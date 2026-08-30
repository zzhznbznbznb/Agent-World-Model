import agent.llm as llm_module


def test_llm_returns_sim_config(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {
                "reply": "已调整森林火灾密度，并提高运行步数。",
                "density": 0.8,
                "steps": 30,
            }

    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
    monkeypatch.setattr(llm_module.requests, "post", lambda *args, **kwargs: DummyResponse())

    model = llm_module.SimpleLLM()
    text, cfg = model.respond("把森林火灾密度调高一点，并运行 30 步", None, return_metadata=True)

    assert "已调整" in text
    assert cfg["density"] == 0.8
    assert cfg["steps"] == 30
