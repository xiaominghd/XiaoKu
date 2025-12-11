"""
@author: Gonghf
@date: 2025/12/7
@description: 
"""
from Memory.memory_manager import *

async def retrieve(memory_bank, event):

    if event is not None:
        result = await memory_bank.get_event_memory(event)

        logger.info(f"检索之后得到的结果为：{result}")

        return None



#
#
#
#
#
# async def main():







