import asyncio

import yaml
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import re
from collections import defaultdict


def extract_code_blocks(markdown_text):
    """
    提取 Markdown 文本中的所有代码块（```包裹的部分）
    返回格式为 {language: [代码块1, 代码块2, ...]}
    """
    # 初始化默认字典
    code_blocks = defaultdict(list)

    # 正则提取代码块，分组：语言名、代码内容
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

    # 匹配所有代码块
    matches = pattern.findall(markdown_text)
    for lang, content in matches:
        lang = lang if lang else 'plain'  # 无语言时用 'plain'
        code_blocks[lang].append(content.strip())

    return dict(code_blocks)


# 为 stdio 连接创建服务器参数
server_params = StdioServerParameters(
    # 服务器执行的命令，这里我们使用 uv 来运行 web_search.py
    command='npx',
    # 运行的参数
    args=['@playwright/mcp@0.0.27',
          '--user-data-dir=./data/mcp-data1'],
    # 环境变量，默认为 None，表示使用当前环境变量
    # env=None
)


async def main():
    # 创建 stdio 客户端
    async with stdio_client(server_params) as (stdio, write):
        # 创建 ClientSession 对象
        async with ClientSession(stdio, write) as session:
            # 初始化 ClientSession
            await session.initialize()

            # 列出可用的工具
            tools = await session.list_tools()
            print(tools)

            # 调用工具
            response = await session.call_tool('browser_navigate', {'url': 'https://www.xiaohongshu.com'})
            for i in response.content[0].text.split('\n'):
                if '- textbox' in i:
                    ref = i.split(' ')[-1].replace('[ref=', '').replace(']', '')
                    break

            print(response)
            search_action = await session.call_tool('browser_type', {"element": "搜索搜索框",
                                                                     "ref": ref,
                                                                     "text": "学英语",
                                                                     "submit": True})
            code_blocks = extract_code_blocks(search_action.content[0].text)
            yaml_block = code_blocks['yaml'][0]
            yaml_loaded = yaml.safe_load(yaml_block)
            content_list = \
                list(list(list(list(list(yaml_loaded[0].values())[0])[1].values())[0][0].values())[0][2].values())[0]
            key = list(content_list[0].keys())[0]
            ref = key.split(' ')[-1].replace('[ref=', '').replace(']', '')
            card_content = await session.call_tool('browser_click', {"element": "card", "ref": ref})
            wait_for = await session.call_tool('browser_wait_for', {"text": "说点什么"})
            search_result = await session.call_tool('browser_snapshot', {})
            print(search_result)


if __name__ == '__main__':
    asyncio.run(main())
