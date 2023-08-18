'''
In this example, a house work robot updates its knowledge about where the fish is.
'''
from agentware.agent_logger import Logger
from agentware.base import PromptProcessor
from agentware.agent import Agent

logger = Logger()
logger.set_level(Logger.DEBUG)

agent_id = "Morphy"
agent = Agent(agent_id)
agent.register(override=True)

story = """乌巢之战是曹操与袁绍两军相争其中一部分,是官渡之战中最重要的一个环节。事件导致袁绍大军无粮食而溃败,曹操实力再为增强。

汉献帝建安五年(200年),曹操得到汉献帝,迁都许昌,于政治上取得优势,并平定多个势力,遂与河北大族袁绍于官渡(今河南中牟县东北)决斗。曹操布下连环计及采用霹雳车,并派出大将关羽,因此多次击败袁军。虽然如此,袁绍军兵多粮足,曹操粮少而将不能支持下去,正巧原本是袁绍麾下谋士的许攸来降,许攸献上奇袭乌巢一计,曹操言听计从,将袁军粮草全部烧毁,情况自此改变。

形势
曹操已经杀死吕布、平定袁术、降服张绣、夺回徐州和击走刘备,收容关羽。而袁绍则把势力强大的公孙瓒消灭,将要与曹操对决,争夺天下。200年,袁绍派陈琳写下檄文,指曹操祖父乃宦官,父亲是乞丐,靠金钱做得高官,曹操则把弄朝中大权,因此要讨伐曹操。袁绍之后先后派颜良、文丑两员大将分别到白马、延津,皆被击败,两将双双被杀。

经过
许攸投降
许攸本是袁绍麾下的谋士,因为贪财而家人被袁绍麾下审配收治,因此投奔曹操。曹操闻讯,说：“子远来了,大事可成！”,以赤脚迎接许攸入座相谈。

许攸问到：“贵军军粮可以用多久？”

曹操答曰：“尚可支持一年。”

许攸再说：“哪有这么多？说真的吧！”

曹操再答：“还可以支持半年。”

许攸说：“难道你不想打败袁绍吗？为何不说真话？”

曹操说：“跟你开玩笑而已,其实军粮只剩此月的份量。”

许攸献计说：“今孟德孤军独守,既无援军,亦无粮食,此乃危急存亡。现在袁军有粮食存于乌巢,虽然有士兵,但无防备,只要派轻兵急袭乌巢,烧其粮草,不过三天,袁军自己败亡！”

奇袭乌巢
曹操听计后大喜,挑选精兵假扮袁军,马含衔枚,士兵拿著柴草向乌巢出发,遇上其他人问话时,皆回答：“袁绍怕曹操奇袭,派我们把守。”袁军不疑有诈,放其通行。到达乌巢后,曹军放火,营中大乱,大破袁军,粮草尽烧,斩领将眭元进、韩莒子、吕威璜、赵叡等首级,割下淳于琼的鼻,杀士卒千馀人,亦将他们的鼻割下,连同牛、马的舌头一同送往袁军,袁军将士大惊。

曹操问败将淳于琼：“你今天弄成这样,是甚么缘故？”

淳于琼答：“胜负乃天所控制的,问我干甚么？”

曹操欲想留下淳于琼性命,许攸指淳于琼日后看到自己的样子必然痛恨曹操,使曹操斩淳于琼。"""
agent.learn(story)

agent = Agent.pull(agent_id)
print(agent.run("曹操和淳于琼是什么关系?"))

# # You can chat with the agent as much as you want on other topics here...
# # And come back to this topic
# agent = Agent.pull(agent_id)
# with agent.update():
#     print("AI response", agent.run("Where is the fish?"))
#     print("AI response:", agent.run(
#         "Ok, I moved the fish to a plate on the table"))

# # You can chat with the agent as much as you want on other topics here...
# # And then ask the agent where is the fish
# agent = Agent.pull(agent_id)
# print("AI response:", agent.run("Where's the fish?"))
