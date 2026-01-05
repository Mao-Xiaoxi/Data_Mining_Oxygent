import asyncio
import logging
from oxygent.oxy.mcp_tools.sse_mcp_client import SSEMCPClient

logging.basicConfig(level=logging.INFO)

async def test_metaso_connection():
    print("Testing Metaso MCP connection...")
    client = SSEMCPClient(
        name="metaso_mcp",
        sse_url="https://metaso.cn/api/mcp",
        headers={
            "Authorization": "Bearer mk-8AA784D355A335948AAA2FE90B222EF4"
        }
    )
    
    try:
        await client.init()
        print("Connection successful!")
        print(f"Tools found: {client.tools}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(test_metaso_connection())
