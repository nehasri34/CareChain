import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from ehr.auth import DEMO_ACCESS
from mcp_server.server import mcp

PATIENT_TOOLS = {
    'get_patient_profile',
    'get_patient_medications',
    'get_patient_allergies',
    'get_patient_diagnoses',
    'get_patient_lab_results',
}


def _unwrap(result):
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
        structured = result[1]
        return structured.get('result', structured)
    if isinstance(result, dict):
        return result.get('result', result)
    if isinstance(result, list) and result:
        item = result[0]
        text = getattr(item, 'text', None)
        if isinstance(text, str):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    return result


def _list_tools():
    return asyncio.run(mcp.list_tools())


def _call(name, **arguments):
    return _unwrap(asyncio.run(mcp.call_tool(name, arguments)))


def test_existing_and_patient_tools_are_registered():
    names = {tool.name for tool in _list_tools()}
    assert 'query_rag' in names
    assert 'ingest_document' in names
    assert PATIENT_TOOLS.issubset(names)
    profile = next(tool for tool in _list_tools() if tool.name == 'get_patient_profile')
    assert 'patient_id' in profile.inputSchema.get('properties', {})
    assert 'user_id' not in profile.inputSchema.get('properties', {})
    assert set(profile.inputSchema.get('required', [])) == {'patient_id'}


def test_get_patient_profile_success(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat001')
    result = _call('get_patient_profile', patient_id='PAT-001')
    assert result['ok'] is True
    assert result['patient_id'] == 'PAT-001'
    assert result['data']['demographics']['full_name'] == 'Mira Langford'


def test_get_patient_medications_and_diagnoses_success(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat001')
    meds = _call('get_patient_medications', patient_id='PAT-001')
    diagnoses = _call('get_patient_diagnoses', patient_id='PAT-001')
    assert meds['ok'] is True
    assert {item['name'] for item in meds['data']} == {'metformin', 'atorvastatin'}
    assert diagnoses['ok'] is True
    assert {item['code'] for item in diagnoses['data']} == {'E11.9', 'E78.5'}


def test_get_patient_lab_results_success(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat001')
    result = _call('get_patient_lab_results', patient_id='PAT-001')
    assert result['ok'] is True
    assert result['data'][0]['unit'] == '%'
    assert result['data'][0]['reference_range'] == '4.0-5.6'


def test_missing_allergies_data(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat002')
    result = _call('get_patient_allergies', patient_id='PAT-002')
    assert result['ok'] is False
    assert result['error'] == 'missing_patient_data'
    assert result['field'] == 'allergies'


def test_unknown_patient(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat001')
    monkeypatch.setitem(
        DEMO_ACCESS,
        'demo-user-pat001',
        frozenset({'PAT-001', 'PAT-999'})
    )
    result = _call('get_patient_profile', patient_id='PAT-999')
    assert result['ok'] is False
    assert result['error'] == 'patient_not_found'
    assert result['patient_id'] == 'PAT-999'


def test_cross_patient_access_denied(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat001')
    result = _call('get_patient_medications', patient_id='PAT-002')
    assert result['ok'] is False
    assert result['error'] == 'patient_access_denied'
    assert result['patient_id'] == 'PAT-002'
    assert result['user_id'] == 'demo-user-pat001'


def test_patient_id_argument_is_not_authorization(monkeypatch):
    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'demo-user-pat003')
    result = _call('get_patient_profile', patient_id='PAT-001')
    assert result['ok'] is False
    assert result['error'] == 'patient_access_denied'


def test_unset_and_unknown_demo_identity(monkeypatch):
    monkeypatch.delenv('CARECHAIN_MCP_DEMO_USER', raising=False)
    missing = _call('get_patient_profile', patient_id='PAT-001')
    assert missing['ok'] is False
    assert missing['error'] == 'unknown_demo_user'

    monkeypatch.setenv('CARECHAIN_MCP_DEMO_USER', 'not-a-user')
    unknown = _call('get_patient_profile', patient_id='PAT-001')
    assert unknown['ok'] is False
    assert unknown['error'] == 'unknown_demo_user'


def test_query_rag_behavior_preserved_with_http_mock(monkeypatch):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        'answer': 'Retain records for 15 years.',
        'sources': [{'document': 'gcp_basics.txt', 'text': 'ICH E6 Good Clinical Practice'}]
    }

    fake_client = MagicMock()
    fake_client.post = AsyncMock(return_value=response)
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)

    import mcp_server.server as server_mod

    monkeypatch.setattr(server_mod.httpx, 'AsyncClient', MagicMock(return_value=fake_client))

    result = _call('query_rag', question='How long must trial records be retained?')
    assert 'Retain records for 15 years.' in result
    assert 'gcp_basics.txt' in result
    fake_client.post.assert_awaited()
    posted = fake_client.post.await_args
    assert posted.args[0].endswith('/chat')
    assert posted.kwargs['json'] == {
        'question': 'How long must trial records be retained?'
    }
