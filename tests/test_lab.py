"""Offline regression tests; fixtures are never written to the submission reports."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import httpx
from langchain_core.messages import AIMessage

import agents
import research
import tools
from check_citations import check
from finalize_citations import finalize


def sources():
    return [{"n": 1, "id": "2501.00001", "url": "https://arxiv.org/abs/2501.00001", "title": "A", "date": "2025-01-01", "source": "arxiv"},
            {"n": 2, "id": "2501.00002", "url": "https://huggingface.co/papers/2501.00002", "title": "B", "date": "2025-01-02", "source": "hf-search"},
            {"n": 3, "id": "https://example.org/c", "url": "https://example.org/c", "title": "C", "date": "n.d.", "source": "web"}]


def report():
    return finalize("# Survey\n\n## TL;DR\nEvidence [1][2][3].", sources())[0]


class CitationTests(unittest.TestCase):
    def test_valid_and_finalizer_idempotent(self):
        self.assertEqual(check(report(), sources()), [])
        finalized, records, problems = finalize(report(), sources())
        self.assertEqual(problems, [])
        self.assertEqual(finalized, report())
        self.assertEqual(records, sources())

    def test_grouped_citations(self):
        for citation in ("[1, 2, 3]", "[1-3]", "[1–3]", "[1, 2-3]"):
            self.assertEqual(check(report().replace("[1][2][3]", citation), sources()), [])

    def test_codes_and_links_do_not_count(self):
        text = report().replace("Evidence [1][2][3].", "Evidence [1][2][3].\n```python\n[90]\n```\n`[91]` [92](https://example.org)")
        self.assertEqual(check(text, sources()), [])
        text = report().replace("Evidence [1][2][3].", "`[1]` [2](https://example.org) [3]")
        self.assertTrue(any("never cited" in p for p in check(text, sources())))

    def test_unknown_and_unused(self):
        self.assertTrue(any("missing" in p for p in check(report().replace("[1][2][3]", "[1][9]"), sources())))
        self.assertTrue(any("never cited" in p for p in check(report().replace("[1][2][3]", "[1]"), sources())))

    def test_invalid_sources(self):
        for value in ([], {}, [None], [{"n": True, "url": []}], [{"n": 1, "url": "https://"}]):
            self.assertTrue(check(report(), value))
        self.assertTrue(check(report(), sources() + [sources()[0]]))

    def test_reference_rules(self):
        for text in (report().replace("## References", "## Bibliography"),
                     report() + "[1] A. https://arxiv.org/abs/2501.00001\n",
                     report().replace("[1] A. arxiv.", "[1] A. https://extra.org arxiv."),
                     report().replace("[1] A. arxiv. https://arxiv.org/abs/2501.00001", "[1] A. arxiv. https://wrong.org"),
                     report() + "## More text\n"):
            self.assertTrue(check(text, sources()))

    def test_only_reference_citations_are_not_enough(self):
        self.assertTrue(check(report().replace("Evidence [1][2][3].", "Evidence."), sources()))


class RetryTests(unittest.TestCase):
    @patch("tools.time.sleep")
    @patch("tools.random.uniform", return_value=0.5)
    def test_backoff_cap_and_success(self, jitter, sleep):
        fn = Mock(side_effect=[tools.RetryableError("temporary"), tools.RetryableError("temporary"), "done"])
        self.assertEqual(tools.with_retry(fn, base=2, cap=4), "done")
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2.5, 4])

    @patch("tools.time.sleep")
    def test_retry_after_and_last_attempt(self, sleep):
        fn = Mock(side_effect=tools.RetryableError("temporary", retry_after=99))
        with self.assertRaises(tools.RetryableError):
            tools.with_retry(fn, attempts=3, cap=10)
        self.assertEqual(fn.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [10, 10])

    @patch("tools.time.sleep")
    def test_permanent_error_is_not_retried(self, sleep):
        fn = Mock(side_effect=ValueError("bad"))
        with self.assertRaises(ValueError):
            tools.with_retry(fn)
        self.assertEqual(fn.call_count, 1)
        sleep.assert_not_called()

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            tools.with_retry(lambda: None, attempts=0)

    @patch("tools.httpx.request")
    def test_http_status_and_transport(self, request):
        request.return_value = httpx.Response(429, headers={"Retry-After": "7"}, request=httpx.Request("GET", tools.ARXIV_URL))
        with self.assertRaises(tools.RetryableError) as context:
            tools._request("GET", tools.ARXIV_URL)
        self.assertEqual(context.exception.retry_after, 7)
        request.return_value = httpx.Response(401, request=httpx.Request("GET", tools.ARXIV_URL))
        with self.assertRaises(httpx.HTTPStatusError):
            tools._request("GET", tools.ARXIV_URL)
        request.side_effect = httpx.ConnectError("offline")
        with self.assertRaises(tools.RetryableError):
            tools._request("GET", tools.ARXIV_URL)


class SourceTests(unittest.TestCase):
    @patch("tools._request")
    def test_empty_queries_skip_network(self, request):
        self.assertEqual(tools.arxiv_search.invoke({"query": '\":: AND OR'}), "NO RESULTS")
        self.assertEqual(tools.hf_search_papers.invoke({"query": " "}), "NO RESULTS")
        self.assertEqual(tools.web_search.invoke({"query": " "}), "NO RESULTS")
        request.assert_not_called()

    @patch("tools._arxiv_request")
    def test_arxiv_xml_and_sanitized_query(self, request):
        request.return_value = SimpleNamespace(text='<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2501.00001v2</id><title> A\n B </title><summary> X  Y </summary><published>2025-01-01T00:00:00Z</published></entry></feed>')
        result = json.loads(tools.arxiv_search.invoke({"query": 'all:\"world model\" AND', "max_results": 99}))
        self.assertEqual(result[0]["url"], sources()[0]["url"])
        self.assertEqual(result[0]["title"], "A B")
        self.assertEqual(request.call_args.args[0]["search_query"], "all:world AND all:model")
        self.assertEqual(request.call_args.args[0]["max_results"], 30)

    @patch("tools.time.sleep")
    @patch("tools.time.monotonic", side_effect=[1, 1, 2, 4])
    @patch("tools._request")
    def test_arxiv_spacing(self, request, monotonic, sleep):
        with patch.object(tools, "_ARXIV_LAST", None):
            tools._arxiv_request({})
            tools._arxiv_request({})
        sleep.assert_called_once_with(2)

    @patch("tools._request")
    def test_hf_mapping_filter_and_search(self, request):
        request.return_value.json.return_value = [{"paper": {"id": "2501.00002", "title": "World model", "summary": "long", "ai_summary": "short", "upvotes": 3}}, {"paper": {"title": "Missing id"}}]
        daily = json.loads(tools.hf_daily_papers.invoke({"keyword": "world"}))
        self.assertEqual(len(daily), 1)
        self.assertEqual(daily[0]["summary"], "long")
        searched = json.loads(tools.hf_search_papers.invoke({"query": "world"}))
        self.assertEqual(searched[0]["summary"], "short")
        self.assertEqual(tools.hf_daily_papers.invoke({"keyword": "absent"}), "NO RESULTS")

    @patch("tools._request")
    @patch("tools.time.sleep")
    def test_exa_sse_rate_limit_retry(self, sleep, request):
        limited = {"result": {"content": [{"type": "text", "text": "please wait"}], "_meta": {"rateLimitExceeded": True, "retryAfter": 2}}}
        good = {"result": {"content": [{"type": "text", "text": "Verified page"}]}}
        request.side_effect = [SimpleNamespace(text="data: " + json.dumps(limited) + "\n\n"), SimpleNamespace(text="data: " + json.dumps(good) + "\n\n")]
        self.assertEqual(tools.web_fetch.invoke({"url": "https://example.org"}), "Verified page")
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(2)
        self.assertEqual(request.call_args.kwargs["json"]["params"]["arguments"], {"urls": ["https://example.org"]})

    @patch("tools._request")
    def test_exa_page_about_rate_limits_is_not_an_error(self, request):
        body = "Title: Rate-limited APIs\nURL: https://example.org/paper\nText: Too many requests cause backoff."
        payload = {"result": {"content": [{"type": "text", "text": body}]}}
        request.return_value = SimpleNamespace(text=json.dumps(payload), json=lambda: payload)
        self.assertEqual(tools.web_fetch.invoke({"url": "https://example.org/paper"}), body)
        self.assertEqual(request.call_count, 1)
        self.assertTrue(tools._rate_limited({}, "ERROR: quota exceeded"))
        self.assertTrue(tools._rate_limited({}, "You have hit the rate limit"))

    @patch("tools._request")
    def test_exa_json_rpc_error_and_redaction(self, request):
        credential = "fixture-value-not-a-real-key"
        with patch.dict(os.environ, {"EXA_API_KEY": credential}):
            request.return_value = SimpleNamespace(text=json.dumps({"error": {"message": f"invalid exaApiKey={credential}"}}))
            result = tools.web_search.invoke({"query": "world"})
            self.assertTrue(result.startswith("ERROR:"))
            self.assertNotIn(credential, result)

    @patch("tools._exa_call", return_value="a" * 20000)
    def test_fetch_length_and_invalid_url(self, call):
        self.assertEqual(len(tools.web_fetch.invoke({"url": "https://example.org"})), 12000)
        self.assertTrue(tools.web_fetch.invoke({"url": "file:///secret"}).startswith("ERROR:"))

    def test_tools_contain_failure(self):
        for fn, args in [(tools.arxiv_search, {"query": "world"}), (tools.hf_daily_papers, {}),
                         (tools.hf_search_papers, {"query": "world"}), (tools.web_search, {"query": "world"}),
                         (tools.web_fetch, {"url": "https://example.org"})]:
            with patch("tools._request", side_effect=ValueError("bad payload")), patch("tools._ARXIV_LAST", None):
                self.assertTrue(fn.invoke(args).startswith("ERROR:"))


class ResearchTests(unittest.TestCase):
    def messages(self):
        return [AIMessage(content="", tool_calls=[{"name": "task", "args": {}, "id": str(n)} for n in range(3)],
                          usage_metadata={"input_tokens": 11, "output_tokens": 4, "total_tokens": 15})]

    def test_slug_and_metadata(self):
        self.assertEqual(research.slugify("../../x"), "x")
        self.assertEqual(research.slugify(" ... "), "topic")
        self.assertEqual(research.slugify("CON"), "topic-con")
        self.assertLessEqual(len(research.slugify("x" * 200)), 60)
        stats = research.summarize(self.messages(), 1.26, "fixture")
        self.assertEqual(stats["subagent_calls"], 3)
        self.assertEqual(stats["tokens"], {"input": 11, "output": 4})
        self.assertEqual(stats["elapsed_s"], 1.3)

    @patch("research.download")
    def test_save_exact_sandbox_bytes(self, download):
        raw_report, raw_sources = report().encode(), json.dumps(sources()).encode()
        download.return_value = {research.REPORT_PATH: raw_report, research.SOURCES_PATH: raw_sources}
        with tempfile.TemporaryDirectory() as directory:
            path = research.save_outputs(None, "Survey", self.messages(), 1, "fixture", directory)
            self.assertEqual(path.read_bytes(), raw_report)
            self.assertEqual(path.with_suffix(".sources.json").read_bytes(), raw_sources)
            self.assertEqual(json.loads(path.with_suffix(".meta.json").read_text())["n_sources"], 3)

    @patch("research.download")
    def test_focused_revision_preserves_measured_runs_and_raw_bytes(self, download):
        raw_report, raw_sources = report().encode(), json.dumps(sources()).encode()
        download.return_value = {research.REPORT_PATH: raw_report, research.SOURCES_PATH: raw_sources}
        original = research.summarize(self.messages(), 12, "original-model")
        followup = [AIMessage(content="", tool_calls=[{"name": "task", "args": {}, "id": "checker"}],
                              usage_metadata={"input_tokens": 7, "output_tokens": 2, "total_tokens": 9})]
        with tempfile.TemporaryDirectory() as directory:
            path = research.save_outputs(None, "Survey", followup, 3, "repair-model", directory,
                                         revision_hash="fixture-hash", prior_meta=original)
            metadata = json.loads(path.with_suffix(".meta.json").read_text())
            self.assertEqual(metadata["subagent_calls"], 4)
            self.assertEqual(metadata["elapsed_s"], 15)
            self.assertEqual(metadata["tokens"], {"input": 18, "output": 6})
            self.assertEqual(metadata["runs"][0], original)
            self.assertEqual(metadata["runs"][1]["subagent_calls"], 1)
            self.assertEqual(path.read_bytes(), raw_report)
            self.assertEqual(path.with_suffix(".sources.json").read_bytes(), raw_sources)

    @patch("research.download")
    def test_failed_save_writes_nothing(self, download):
        for payload in ({}, {research.REPORT_PATH: b"", research.SOURCES_PATH: b"[]"},
                        {research.REPORT_PATH: report().encode(), research.SOURCES_PATH: b"not JSON"},
                        {research.REPORT_PATH: report().encode(), research.SOURCES_PATH: b"[]"}):
            download.return_value = payload
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(RuntimeError):
                    research.save_outputs(None, "Survey", self.messages(), 1, "fixture", directory)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_publish_failure_restores_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "a").write_bytes(b"old")
            original = os.replace
            count = 0
            def replace(a, b):
                nonlocal count
                count += 1
                if count == 2:
                    raise OSError("disk error")
                return original(a, b)
            with patch("research.os.replace", side_effect=replace):
                with self.assertRaises(OSError):
                    research._publish_files(directory, {"a": b"new", "b": b"new"})
            self.assertEqual((directory / "a").read_bytes(), b"old")
            self.assertFalse((directory / "b").exists())

    def test_provenance_and_finalizer_loss_of_family(self):
        records = sources()
        records[0]["url"] = "https://example.org/a"
        self.assertTrue(research._source_problems(records))

    def test_source_dates_reject_invented_partial_formats_and_invalid_days(self):
        for date in ("2024-n.d.", "2026-02-30", "2024-1-1", 2024):
            records = sources()
            records[0]["date"] = date
            self.assertTrue(any("source date" in error for error in research._source_problems(records)))
        for date in ("n.d.", "2024-02-29"):
            records = sources()
            records[0]["date"] = date
            self.assertEqual(research._source_problems(records), [])

    def completion_messages(self):
        calls = [{"name": "task", "args": {"subagent_type": "researcher"}, "id": str(n)} for n in range(3)]
        calls += [{"name": "task", "args": {"subagent_type": "citation-checker"}, "id": "checker"},
                  {"name": "execute", "args": {"command": f"python3 {agents.FINALIZER_PATH}"}, "id": "finalize"},
                  {"name": "execute", "args": {"command": f"python3 {agents.VALIDATOR_PATH}"}, "id": "validate"}]
        return [AIMessage(content="", tool_calls=calls)]

    @patch("research.download")
    def test_postflight_accepts_complete_contract(self, download):
        text = report().replace("## TL;DR", "## Background\n## Theme A\n## Theme B\n## Theme C\n## Trends and open problems\n## TL;DR")
        download.return_value = {research.REPORT_PATH: text.encode(), research.SOURCES_PATH: json.dumps(sources()).encode(),
                                 agents.NOTES_DIR + "/citation-audit.md": b"SUPPORTED"}
        self.assertEqual(research._completion_problems(None, self.completion_messages()), [])

    @patch("research.download")
    def test_postflight_catches_family_url_and_missing_audit(self, download):
        records = sources()
        records[1]["url"] = "https://arxiv.org/html/2501.00002"
        text = finalize("Claim [1][2][3].", records)[0]
        download.return_value = {research.REPORT_PATH: text.encode(), research.SOURCES_PATH: json.dumps(records).encode()}
        problems = research._completion_problems(None, [])
        self.assertTrue(any("HF source" in p for p in problems))
        self.assertTrue(any("citation-audit" in p for p in problems))
        self.assertTrue(any("researcher" in p for p in problems))

    @patch("research.save_outputs", return_value=Path("fixture.md"))
    @patch("research._completion_problems", side_effect=[["HF source URL mismatch"], []])
    @patch("research.build_lead_agent")
    @patch("research._configured_sandbox")
    @patch("research.download")
    @patch("research.upload")
    @patch("research.make_model")
    def test_main_repairs_in_same_sandbox_with_real_history(self, model, upload, download, sandbox, build, problems, save):
        backend = Mock()
        backend.execute.return_value = SimpleNamespace(exit_code=0, output="OK: fixtures")
        sandbox.return_value.__enter__.return_value = backend
        download.return_value = {agents.VALIDATOR_PATH: research.VALIDATOR_SOURCE.read_bytes(),
                                 agents.FINALIZER_PATH: research.FINALIZER_SOURCE.read_bytes()}
        history = self.completion_messages()
        agent = Mock()
        agent.invoke.return_value = {"messages": history}
        build.return_value = agent
        self.assertEqual(research.main("Fixture topic"), 0)
        self.assertEqual(agent.invoke.call_count, 2)
        repaired_input = agent.invoke.call_args.args[0]
        self.assertIs(repaired_input["messages"][0], history[0])
        self.assertIn("HF source URL mismatch", repaired_input["messages"][-1]["content"])
        self.assertEqual(sandbox.call_count, 1)
        sandbox.return_value.__exit__.assert_called_once()
        text, records, errors = finalize("Only one [1].", sources())
        self.assertFalse(errors)
        self.assertTrue(research._source_problems(records))

    @patch("research.make_model", side_effect=RuntimeError("not configured"))
    def test_main_exit_codes(self, model):
        self.assertEqual(research.main(" "), 2)
        self.assertEqual(research.main("Survey"), 1)

    def test_revision_seeds_original_bytes_and_measures_new_history(self):
        backend = Mock()
        backend.execute.return_value = SimpleNamespace(exit_code=0, output="OK: fixture")
        manager = MagicMock()
        manager.__enter__.return_value = backend
        history = self.completion_messages()
        agent = Mock()
        agent.invoke.return_value = {"messages": history}
        raw = {agents.REPORT_PATH: report().encode(), agents.SOURCES_PATH: json.dumps(sources()).encode()}
        scripts = {agents.VALIDATOR_PATH: research.VALIDATOR_SOURCE.read_bytes(),
                   agents.FINALIZER_PATH: research.FINALIZER_SOURCE.read_bytes(), **raw}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.md").write_bytes(raw[agents.REPORT_PATH])
            (root / "fixture.sources.json").write_bytes(raw[agents.SOURCES_PATH])
            with patch.multiple(research, REPORTS=root, make_model=Mock(),
                                _configured_sandbox=Mock(return_value=manager), download=Mock(return_value=scripts),
                                _completion_problems=Mock(return_value=[]), build_lead_agent=Mock(return_value=agent)), \
                    patch("research.upload") as upload, patch("research.save_outputs", return_value=Path("fixture.md")) as save:
                self.assertEqual(research.main("Fixture", "Verify the exact metric.", revise=True), 0)
                self.assertEqual(upload.call_args_list[1].args[1], raw)
                self.assertIs(save.call_args.args[2], history)
                self.assertEqual(save.call_args.kwargs["revision_hash"], research.hashlib.sha256(raw[agents.REPORT_PATH]).hexdigest())
                self.assertIn("Verify the exact metric.", agent.invoke.call_args.args[0]["messages"][0]["content"])
        manager.__exit__.assert_called_once()

    @patch("agents.create_deep_agent")
    def test_all_agents_are_bounded(self, create):
        agents.build_lead_agent("backend", "model")
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["backend"], "backend")
        for spec in kwargs["subagents"]:
            self.assertEqual(len(spec["middleware"]), 4)
        self.assertEqual(len(kwargs["middleware"]), 5)

    def test_guard_rejects_shortcuts_and_script_tampering(self):
        guard = agents.WorkspaceGuard()
        for call in [{"name": "write_file", "args": {"file_path": agents.VALIDATOR_PATH}},
                     {"name": "edit_file", "args": {"file_path": agents.NOTES_DIR + "/../check_citations.py"}},
                     {"name": "write_file", "args": {"file_path": "/tmp/work/report/sources.json"}},
                     {"name": "execute", "args": {"command": "python3 /tmp/custom_checker.py"}},
                     {"name": "execute", "args": {"command": f"python3 {agents.VALIDATOR_PATH}; echo OK"}}]:
            self.assertTrue(guard._problem(call))
        for call in [{"name": "execute", "args": {"command": f"python3 {agents.VALIDATOR_PATH}"}},
                     {"name": "write_file", "args": {"file_path": agents.SOURCES_PATH}},
                     {"name": "edit_file", "args": {"file_path": agents.REPORT_PATH}},
                     {"name": "write_file", "args": {"file_path": agents.NOTES_DIR + "/01.md"}}]:
            self.assertIsNone(guard._problem(call))

    @patch("agents.time.sleep")
    def test_model_retry_and_daily_quota(self, sleep):
        middleware = agents.TemporaryModelRetry()
        handler = Mock(side_effect=[RuntimeError("429 Please retry in 12s."), "done"])
        self.assertEqual(middleware.wrap_model_call(None, handler), "done")
        sleep.assert_called_once_with(14)
        self.assertIsNone(agents._model_retry_delay(RuntimeError("429 GenerateRequestsPerDay limit: 20")))
        self.assertIsNone(agents._model_retry_delay(RuntimeError("401 invalid API key")))
        handler = Mock(side_effect=RuntimeError("503 UNAVAILABLE"))
        with self.assertRaises(RuntimeError):
            middleware.wrap_model_call(None, handler)
        self.assertEqual(handler.call_count, 3)

    @patch("research.sandbox_kind", return_value="daytona")
    @patch("research.open_sandbox")
    def test_daytona_creation_failure_falls_back_and_cleans_up(self, factory, kind):
        first, second = MagicMock(), MagicMock()
        first.__enter__.side_effect = RuntimeError("unavailable")
        second.__enter__.return_value = "docker-backend"
        factory.side_effect = [first, second]
        with patch.dict(os.environ, {"SANDBOX_FALLBACK": "docker"}):
            with research._configured_sandbox() as backend:
                self.assertEqual(backend, "docker-backend")
        self.assertEqual(factory.call_args_list[1].args, ("docker",))
        second.__exit__.assert_called_once_with(None, None, None)

    @patch("research.open_sandbox")
    def test_agent_failure_cleans_up_without_fallback(self, factory):
        manager = MagicMock()
        factory.return_value = manager
        with self.assertRaisesRegex(ValueError, "agent failed"):
            with research._configured_sandbox():
                raise ValueError("agent failed")
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(manager.__exit__.call_args.args[0], ValueError)


if __name__ == "__main__":
    unittest.main()
