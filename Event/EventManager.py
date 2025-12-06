"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import statistics
import re
from Event import *
from typing import List

class ConversationInterestAnalyzer:
    """对话兴趣度分析器"""

    # 兴趣度阈值配置
    INTEREST_THRESHOLDS = {
        'response_time_factor': 1.5,  # 响应时间超过中位数的倍数
        'min_word_count': 6,  # 最小有效字数
        'max_short_responses': 2,  # 连续简短回复的最大次数
        'time_window_minutes': 30,  # 时间窗口
    }

    @staticmethod
    def get_conversation_interest_level(messages: List[SingleContext]) -> Dict:
        """
        综合评估对话兴趣度

        Returns:
            Dict: 包含各项指标和最终判断
        """
        # 过滤出有效用户消息
        valid_user_messages = ConversationInterestAnalyzer._filter_valid_user_messages(messages)

        if len(valid_user_messages) < 3:
            return {
                'interest_level': 'insufficient_data',
                'reason': '有效对话轮次不足',
                'details': {
                    'valid_rounds': len(valid_user_messages),
                    'required_rounds': 3
                }
            }

        # 计算各项指标
        metrics = ConversationInterestAnalyzer._calculate_metrics(valid_user_messages)

        # 综合评估兴趣度
        interest_level, reasons = ConversationInterestAnalyzer._evaluate_interest_level(metrics)

        return {
            'interest_level': interest_level,
            'reasons': reasons,
            'metrics': metrics,
            'suggestions': ConversationInterestAnalyzer._generate_suggestions(metrics, interest_level)
        }

    @staticmethod
    def _filter_valid_user_messages(messages: List[SingleContext]) -> List[SingleContext]:
        """过滤出有效用户消息"""
        filtered = []

        for message in messages:
            if message.role != "user":
                continue

            # 排除系统消息和特殊标记的消息
            if any(marker in message.content for marker in ["[系统上下文开始]", "[指引信息开始]"]):
                continue

            # 排除纯表情、标点等无效内容
            if ConversationInterestAnalyzer._is_meaningless_content(message.content):
                continue

            filtered.append(message)

        return filtered

    @staticmethod
    def _is_meaningless_content(content: str) -> bool:
        """判断内容是否无意义"""
        # 去除空格和特殊字符
        cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '', content)

        # 检查是否为纯表情、数字或单个字符
        if len(cleaned) == 0:
            return True

        # 检查是否为常见无意义回复
        meaningless_patterns = [
            '哦', '嗯', '好的', '知道了', '行', 'OK', 'ok', 'Ok',
            '好', '对', '是的', '是', '不是', '没有'
        ]

        if cleaned in meaningless_patterns or len(cleaned) <= 2:
            return True

        return False

    @staticmethod
    def _calculate_metrics(messages: List[SingleContext]) -> Dict:
        """计算各项指标"""
        metrics = {
            'total_rounds': len(messages),
            'response_times': [],
            'word_counts': [],
            'content_patterns': [],
            'timestamps': []
        }

        # 按时间排序
        messages.sort(key=lambda x: x.create_time)

        # 计算响应时间和字数
        for i in range(1, len(messages)):
            time_diff = (messages[i].create_time - messages[i - 1].create_time).total_seconds()
            word_count = len(messages[i].content.strip())

            metrics['response_times'].append(time_diff)
            metrics['word_counts'].append(word_count)
            metrics['content_patterns'].append({
                'round': i,
                'content': messages[i].content[:50] + '...' if len(messages[i].content) > 50 else messages[i].content,
                'word_count': word_count
            })
            metrics['timestamps'].append(messages[i].create_time)

        # 计算统计指标
        if metrics['response_times']:
            metrics['response_time_median'] = statistics.median(metrics['response_times'])
            metrics['response_time_mean'] = statistics.mean(metrics['response_times'])
            metrics['word_count_median'] = statistics.median(metrics['word_counts'])
            metrics['word_count_mean'] = statistics.mean(metrics['word_counts'])

        # 分析最近几轮的趋势
        metrics.update(ConversationInterestAnalyzer._analyze_recent_trends(
            metrics['response_times'],
            metrics['word_counts']
        ))

        # 分析内容质量
        metrics['content_quality'] = ConversationInterestAnalyzer._analyze_content_quality(
            [m.content for m in messages[-3:]]  # 最近3条消息
        )

        return metrics

    @staticmethod
    def _analyze_recent_trends(response_times: List[float], word_counts: List[int]) -> Dict:
        """分析最近趋势"""
        recent_n = min(3, len(response_times))

        if recent_n == 0:
            return {
                'recent_avg_response_time': 0,
                'recent_avg_word_count': 0,
                'response_time_trend': 'stable',
                'word_count_trend': 'stable'
            }

        # 最近N轮
        recent_response_times = response_times[-recent_n:]
        recent_word_counts = word_counts[-recent_n:]

        # 历史数据（排除最近N轮）
        historical_response_times = response_times[:-recent_n] if len(response_times) > recent_n else response_times
        historical_word_counts = word_counts[:-recent_n] if len(word_counts) > recent_n else word_counts

        # 计算趋势
        response_time_trend = ConversationInterestAnalyzer._calculate_trend(
            recent_response_times, historical_response_times
        )

        word_count_trend = ConversationInterestAnalyzer._calculate_trend(
            recent_word_counts, historical_word_counts, is_word_count=True
        )

        return {
            'recent_avg_response_time': statistics.mean(recent_response_times) if recent_response_times else 0,
            'recent_avg_word_count': statistics.mean(recent_word_counts) if recent_word_counts else 0,
            'historical_avg_response_time': statistics.mean(
                historical_response_times) if historical_response_times else 0,
            'historical_avg_word_count': statistics.mean(historical_word_counts) if historical_word_counts else 0,
            'response_time_trend': response_time_trend,
            'word_count_trend': word_count_trend
        }

    @staticmethod
    def _calculate_trend(recent: List, historical: List, is_word_count: bool = False) -> str:
        """计算趋势"""
        if not recent or not historical:
            return 'insufficient_data'

        recent_avg = statistics.mean(recent)
        historical_avg = statistics.mean(historical)

        if historical_avg == 0:
            return 'unstable'

        if is_word_count:
            # 字数趋势：下降表示兴趣减弱
            if recent_avg < historical_avg * 0.5:
                return 'sharp_decrease'
            elif recent_avg < historical_avg * 0.8:
                return 'decrease'
            elif recent_avg > historical_avg * 1.2:
                return 'increase'
            else:
                return 'stable'
        else:
            # 响应时间趋势：上升表示兴趣减弱
            if recent_avg > historical_avg * 2.0:
                return 'sharp_increase'
            elif recent_avg > historical_avg * 1.5:
                return 'increase'
            elif recent_avg < historical_avg * 0.7:
                return 'decrease'
            else:
                return 'stable'

    @staticmethod
    def _analyze_content_quality(recent_contents: List[str]) -> Dict:
        """分析内容质量"""
        quality_scores = []
        patterns = []

        for content in recent_contents:
            score = 0

            # 长度得分
            if len(content) > 100:
                score += 3
            elif len(content) > 50:
                score += 2
            elif len(content) > 20:
                score += 1

            # 问题质量得分（是否包含问号、疑问词）
            if any(q_word in content for q_word in ['?', '？', '什么', '如何', '为什么', '怎么', '能否']):
                score += 2

            # 具体性得分（是否包含具体名词、数字）
            if re.search(r'\d+', content) or len(re.findall(r'[A-Za-z\u4e00-\u9fff]{2,}', content)) > 5:
                score += 1

            quality_scores.append(score)

            # 记录模式
            if score >= 3:
                patterns.append('high_quality')
            elif score >= 1:
                patterns.append('medium_quality')
            else:
                patterns.append('low_quality')

        return {
            'scores': quality_scores,
            'avg_score': statistics.mean(quality_scores) if quality_scores else 0,
            'patterns': patterns,
            'trend': 'improving' if len(quality_scores) >= 2 and quality_scores[-1] > quality_scores[0] else 'declining'
        }

    @staticmethod
    def _evaluate_interest_level(metrics: Dict) -> Tuple[str, List[str]]:
        """评估兴趣度水平"""
        reasons = []
        warning_count = 0

        # 检查响应时间趋势
        if metrics.get('response_time_trend') in ['increase', 'sharp_increase']:
            time_factor = metrics['recent_avg_response_time'] / metrics['historical_avg_response_time'] if metrics[
                                                                                                               'historical_avg_response_time'] > 0 else 1
            if time_factor > 1.5:
                reasons.append(f"响应时间显著增加 ({time_factor:.1f}倍)")
                warning_count += 1

        # 检查字数趋势
        if metrics.get('word_count_trend') in ['decrease', 'sharp_decrease']:
            word_factor = metrics['recent_avg_word_count'] / metrics['historical_avg_word_count'] if metrics[
                                                                                                         'historical_avg_word_count'] > 0 else 1
            if word_factor < 0.7:
                reasons.append(f"回复字数显著减少 ({word_factor:.1f}倍)")
                warning_count += 1

        # 检查内容质量
        if metrics.get('content_quality', {}).get('avg_score', 0) < 1:
            reasons.append("最近回复内容质量较低")
            warning_count += 1

        # 检查是否有连续简短回复
        short_count = sum(1 for wc in metrics.get('word_counts', [])[-3:] if wc < 10)
        if short_count >= 2:
            reasons.append(f"最近{len(metrics.get('word_counts', [])[-3:])}轮中有{short_count}次简短回复")
            warning_count += 1

        # 判断兴趣度水平
        if warning_count >= 2:
            return 'low', reasons
        elif warning_count == 1:
            return 'medium', reasons
        else:
            return 'high', ['对话参与度良好']

    @staticmethod
    def _generate_suggestions(metrics: Dict, interest_level: str) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if interest_level == 'low':
            suggestions.append("用户参与度较低，建议尝试：")
            suggestions.append("1. 提出开放性问题引导用户")
            suggestions.append("2. 分享相关案例或故事")
            suggestions.append("3. 确认用户的具体需求")

        elif interest_level == 'medium':
            suggestions.append("用户参与度中等，建议：")
            suggestions.append("1. 检查回复是否解决了用户的核心问题")
            suggestions.append("2. 提供更具体的建议或方案")
            suggestions.append("3. 使用更积极的沟通语气")

        # 具体问题具体建议
        if metrics.get('word_count_trend') == 'sharp_decrease':
            suggestions.append("检测到用户回复变简短，可能需要：")
            suggestions.append("- 避免使用专业术语")
            suggestions.append("- 将复杂问题分解")
            suggestions.append("- 询问用户是否理解")

        if metrics.get('response_time_trend') == 'sharp_increase':
            suggestions.append("检测到用户响应变慢，建议：")
            suggestions.append("- 适当总结对话要点")
            suggestions.append("- 确认用户是否在线")
            suggestions.append("- 提供多种解决方案供选择")

        return suggestions if suggestions else ["继续保持当前沟通方式"]

class EventBank:

    def __init__(self, current_event:Event=None):

        self.current_event = current_event

        self.prepared_events = []

        self.finished_events = []

        self.prepared_events_mapper = {}

    def init_event_list(self, event_list:List[Event]):
        self.current_event = event_list[0]

        self.prepared_events = event_list[1:]

        for event in event_list:
            self.prepared_events_mapper[event.name]=event


    async def update(self, event_name:str):

        event = self.prepared_events_mapper[event_name]  # 通过映射表的方式找到当前数据

        self.current_event = event  # 当前事件需要进行一次总结
        self.finished_events.append(event)


        # 更新候选话题
        self.prepared_events = [event for event in self.prepared_events if event != self.current_event]

        # 更新已经完成的话题
        self.finished_events = [event for event in self.finished_events if event != self.current_event]

    async def check_current_conversation(self, message: SingleContext):

        history = self.current_event.history.trans_cache2openai()

        history = history + [{"role":message.role, "content":message.content}]

        conversation_str = history
        # 将当前的会话与之前的对话进行拼接

        other_event = [e.name for e in self.prepared_events + self.finished_events]

        other_event_str = "\n".join(other_event)

        prompt = f"""# 任务说明

## 核心目标
根据当前对话内容准确判断用户正在讨论的话题。

## 话题判断规则

### 1. 话题保持条件
当出现以下情况时，应保持当前话题不变：
- 用户和助手正在进行无实质内容的闲聊
- 对话内容仍然围绕当前话题展开
- 用户只是对当前话题进行补充、延伸或细化
- 对话中出现简单的回应、确认或社交性表达

### 2. 话题切换条件
**只有当用户明确表达切换意图时**，才认定为话题切换。明确意图包括：
- 直接声明："让我们换个话题吧"、"我们聊点别的"
- 明确提问新领域："你知道XXX吗？"、"我们讨论一下YYY"
- 使用转折词引入全新内容："话说回来..."、"另外..."，且后面跟随的是与当前话题无关的新内容

### 3. 话题延伸的定义
以下情况视为话题延伸，仍属于同一话题：
- 从主话题自然延伸到相关子话题（科技→人工智能）
- 在原有话题范围内进行深入讨论
- 举例说明或补充相关信息
- 话题的细化或具体化

### 4. 结束对话条件
当用户明确表达结束对话的意图时，应返回"结束"。明确意图包括：
- 直接告别："再见"、"拜拜"、"下次聊"
- 表达结束意愿："不想聊了"、"结束对话"、"就到这里吧"
- 其他明确的结束性话语

## 输出要求
- 仅输出话题名称或"结束"
- 优先匹配备选话题名称列表中的最接近项
- 若无匹配项，创建简短准确的话题名称总结
- 如果用户表达了结束对话意图，输出"结束"
- 如果用户表达了切换话题意图但未指定具体话题，默认返回其他话题列表中的第一个话题
- 话题名称应简洁明了，体现核心内容

## 输入信息
用户和助手的对话：{conversation_str}
用户和助手当前的话题（话题名称：话题总结）：
{self.current_event.name}:{self.current_event.summary}
用户和助手的其他话题名称列表：
{other_event_str}

## 处理流程
1. 首先判断是否有明确的结束对话意图：
   - 如有，输出"结束"
   - 如无，继续下一步
2. 判断是否有明确的话题切换意图：
   - 如无切换意图，检查是否属于当前话题的延伸或闲聊：
     - 如果是，保持当前话题
     - 如果否，可能为新话题，进入步骤3
3. 如有切换意图：
   - 如果用户指定了新话题内容，在备选话题名称列表中寻找最佳匹配：
     - 若找到匹配，返回该话题名称
     - 若无匹配，创建合适的话题名称
   - 如果用户未指定新话题（如只说"换个话题"但未说换什么），默认返回其他话题列表中的第一个话题
请你只输出当前话题的名称，除此之外不要输出其他任何信息。
"""

        answer = get_qwen_max_answer(prompt)
        print(f"当前的话题为：{answer}")
        print(self.current_event.name)

        if answer == self.current_event.name:
            await self.current_event.history.append_context(message)

        if answer in other_event:  # 当前正在进行状态切换

            logger.info(f"将当前话题：{self.current_event.name} 切换至 {answer}")

            await self.update(answer)  # 仅调整位置

            await self.current_event.history.append_context(message)

            return self.prepared_events_mapper[answer]  # 返回的数据类型是不同的


        elif answer not in other_event and answer != self.current_event.name:  # 当前正在创建新事件

            new_event = Event(name=answer)

            self.prepared_events_mapper[answer] = new_event

            self.finished_events.append(self.current_event)
            self.current_event = new_event

            await self.current_event.history.append_context(message)

            return self.prepared_events_mapper[answer]

    async def get_conversation_guide(self):
        conversations = []
        for message in self.current_event.history.cache[2:]:

            if any(marker in message.content for marker in ["[系统上下文开始]", "[指引信息开始]","[系统上下文结束]"]):
                continue

            else:

                conversations.append(message)

        if len(conversations) < 3:
            return None

        conversation_str = "\n".join([f"role:{conversation.role}, content:{conversation.content}"
                            for conversation in conversations[-10:]])
        prompt = f"""你是一个专业的对话分析助手，请根据提供的用户与助手的历史对话内容，生成结构化指引，以提升用户参与积极性，并引导助手进行更有效的互动。

请从以下三个维度进行分析并提供建议，并确保输出为**纯JSON格式**：

## 1. 回复建议（需要立即回应的问题）
- 评估助手是否充分关注用户的情感与需求
- 检查是否有误解用户意图或信息遗漏
- 针对当前对话轮次，给出具体、亲切的回应方向建议

## 2. 对话目标（远期互动方向）
- 基于当前话题，推荐2-3个用户可能感兴趣的子话题或延伸方向
- 从对话中提取用户潜在画像特征（如兴趣、身份、需求等）
- 提供自然过渡到新话题的对话策略

## 3. 注意事项（互动执行建议）
- 提供具体话术或提问示例，增强对话引导性
- 建议如何平衡信息提供与用户参与度
- 避免机械问答，增加开放性与情感共鸣点

## 输出要求
- 仅返回一个JSON对象，格式严格如下，除此之外不要输出其他任何信息：
{{
  "回复": "针对当前对话的立即回应建议",
  "目标": "远期互动方向与用户画像分析",
  "注意": "具体执行建议与话术示例"
}}

用户和助手的对话如下：
{conversation_str}"""

        answer = await get_deepseek_answer(message=prompt)
        return answer

    def check_conversation_interest(self):

        # 根据当前对话响应情况快速判断用户的感兴趣程度
        # 兼具时间判据以及当前回复的判据
        analysis = (
            ConversationInterestAnalyzer.get_conversation_interest_level(self.current_event.history.cache))

        if analysis['interest_level'] != "high":

            return True
        else:

            return False


# 使用示例
if __name__ == "__main__":
    # 模拟对话数据
    conversation = [
        SingleContext(datetime.now() - timedelta(minutes=30), 'user', '你好，我想了解Python编程的学习路径。'),
        SingleContext(datetime.now() - timedelta(minutes=29), 'assistant', '当然！Python学习可以从基础语法开始...'),
        SingleContext(datetime.now() - timedelta(minutes=28), 'user',
                      '那具体应该学习哪些内容呢？能给我一个详细的大纲吗？'),
        SingleContext(datetime.now() - timedelta(minutes=27), 'assistant',
                      '好的，一个完整的Python学习大纲包括：1.基础语法 2.数据结构...'),
        SingleContext(datetime.now() - timedelta(minutes=25), 'user', '听起来不错。'),
        SingleContext(datetime.now() - timedelta(minutes=24), 'assistant', '您希望从哪个部分开始深入了解？'),
        SingleContext(datetime.now() - timedelta(minutes=23), 'user', '嗯。'),
        SingleContext(datetime.now() - timedelta(minutes=22), 'assistant', '或者您有具体的项目想法吗？'),
        SingleContext(datetime.now() - timedelta(minutes=20), 'user', '再想想。'),
    ]

    # 分析对话兴趣度
    analysis = ConversationInterestAnalyzer.get_conversation_interest_level(conversation)

    print(f"兴趣度等级: {analysis['interest_level']}")
    print(f"\n原因分析:")
    for reason in analysis['reasons']:
        print(f"- {reason}")

    print(f"\n详细指标:")
    print(f"总有效轮次: {analysis['metrics'].get('total_rounds', 0)}")
    print(f"响应时间趋势: {analysis['metrics'].get('response_time_trend', 'N/A')}")
    print(f"字数趋势: {analysis['metrics'].get('word_count_trend', 'N/A')}")
    print(f"最近平均字数: {analysis['metrics'].get('recent_avg_word_count', 0):.1f}")
    print(f"内容质量评分: {analysis['metrics'].get('content_quality', {}).get('avg_score', 0):.1f}")

    print(f"\n改进建议:")
    for suggestion in analysis['suggestions']:
        print(f"- {suggestion}")

