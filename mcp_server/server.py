import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import httpx
from mcp_server.ehr_tools import (
    get_patient_allergies_tool,
    get_patient_diagnoses_tool,
    get_patient_lab_results_tool,
    get_patient_medications_tool,
    get_patient_profile_tool,
)

mcp = FastMCP('ClinicalRAG')
API_URL = "http://localhost:8000"

@mcp.tool()
async def query_rag(question: str) -> str:
    """Ask a question over indexed clinical documents."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'{API_URL}/chat',
            json={'question': question},
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()

    answer = data['answer']
    sources = data['sources']

    source_lines = []
    for source in sources:
        doc = source['document']
        preview = source['text'][:100]
        source_lines.append(f"{doc}: {preview}")

    sources_text = "\n".join(source_lines)

    return f"{answer}\nSources:\n{sources_text}"

@mcp.tool()
async def ingest_document(file_path: str) -> str:
    """Ingest a text file into the clinical RAG system.
    The file_path must be an absolute path on the local machine
    where the MCP server is running.
    Example: C:\\Users\\stela\\Coding\\projects\\clinical-rag\\data\\samples\\file.txt
    """
    path = Path(file_path)

    async with httpx.AsyncClient() as client:
        with open(path, 'rb') as f:
            upload = (path.name, f, 'text/plain')
            response = await client.post(
                f'{API_URL}/documents/ingest',
                files={'file': upload},
                timeout=60.0
            )
        response.raise_for_status()
        data = response.json()

    return f"Indexed {data['filename']} into {data['chunks']} chunks."


@mcp.tool(name='get_patient_profile')
def get_patient_profile(patient_id: str) -> dict:
    """Read-only: return the fictional patient's profile.

    Authorization uses the MCP server process identity
    (CARECHAIN_MCP_DEMO_USER). patient_id is not authorization.
    """
    return get_patient_profile_tool(patient_id)


@mcp.tool(name='get_patient_medications')
def get_patient_medications(patient_id: str) -> dict:
    """Read-only: return the fictional patient's medications.

    Authorization uses CARECHAIN_MCP_DEMO_USER, not patient_id.
    """
    return get_patient_medications_tool(patient_id)


@mcp.tool(name='get_patient_allergies')
def get_patient_allergies(patient_id: str) -> dict:
    """Read-only: return the fictional patient's allergies.

    Authorization uses CARECHAIN_MCP_DEMO_USER, not patient_id.
    """
    return get_patient_allergies_tool(patient_id)


@mcp.tool(name='get_patient_diagnoses')
def get_patient_diagnoses(patient_id: str) -> dict:
    """Read-only: return the fictional patient's diagnoses.

    Authorization uses CARECHAIN_MCP_DEMO_USER, not patient_id.
    """
    return get_patient_diagnoses_tool(patient_id)


@mcp.tool(name='get_patient_lab_results')
def get_patient_lab_results(patient_id: str) -> dict:
    """Read-only: return the fictional patient's lab results.

    Authorization uses CARECHAIN_MCP_DEMO_USER, not patient_id.
    """
    return get_patient_lab_results_tool(patient_id)

if __name__ == '__main__':
    mcp.run()
