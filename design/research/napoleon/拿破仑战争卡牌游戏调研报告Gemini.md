# **拿破仑战争主题策略卡牌游戏（PC端）MVP 阶段详尽调研与立项报告**

## **一、 对标竞品深度拆解与系统映射分析**

在构筑拿破仑战争主题策略卡牌游戏（CCG）的基石时，对《Kards: The WWII Card Game》的系统性拆解提供了不可或缺的参照。该作成功将宏大的二战军事逻辑抽象为严密的卡牌博弈机制，其设计决策及长线运营数据为本项目的开发指明了方向并揭示了潜在的系统性风险。

### **1\. 机制层的资源与战场博弈逻辑**

《Kards》的核心系统创新在于将传统卡牌游戏中的单一法力值体系，拆分为“部署（Deployment）”与“行动（Operation）”的双轨成本，并引入了单线争夺的“前线（Frontline）”概念，这一系列设计深刻影响了游戏的底层节奏。  
该游戏的资源系统被称为指挥点（Kredits），其初始值为一点，每回合自然增长一点，上限固定为十二点 1。这种设计为游戏提供了稳定且可预期的基础节奏，但特定阵营（尤其是美国阵营）能够通过特殊的跳费机制（Ramp）打破这种线性增长，从而提前部署高费用的战争机器 2。在具体的对局中，玩家打出单位牌时需支付部署费用，而后续移动单位至前线或发起攻击则需额外支付行动费用 1。这一机制在游戏语境中完美模拟了军事后勤补给与前线指令传达的延迟，迫使玩家在有限的资源下，在“扩大军队规模（铺场）”与“发起战术打击（进攻）”之间进行极其痛苦且深度的资源分配博弈。  
在战场结构的设计上，《Kards》摒弃了传统CCG的对称双排模式，转而采用由双方各自的支援线（Support Line，各包含五个空位）与全局唯一的公共前线（Frontline，包含五个空位）组成的三线结构 4。前线在同一时间仅能被交战双方中的一方所控制。占据前线的单位获得了极大的战术优势，不仅能够直接攻击敌方位于支援线的单位，更能够直接威胁敌方的指挥部（HQ） 4。这一机制塑造了极其强烈的“拉锯战”与“阵地争夺”体验。与之相配套的突破（Smash）机制则允许高攻击力单位在消灭敌方守军后，将多余的伤害直接穿透至敌方基地，进一步放大了抢夺前线的收益。  
指挥部（HQ）机制构成了游戏的终结条件。每个HQ的初始血量通常设定为二十点。当且仅当敌方前线没有任何防守单位，或者己方已经完全控制前线，抑或是玩家使用具有远程跨线打击能力的单位（例如轰炸机或特定火炮）时，才可以对敌方HQ进行直接攻击 1。这种设定极大地限制了快攻卡组无视场面直接“打脸”的策略，强制玩家必须进行单位间的交换。  
在单位类型与克制关系的构建上，游戏抽象出了五大核心兵种。步兵（Infantry）作为基础占场单位，造价低廉且承担主要的防线填补工作；坦克（Tank）通常具有重甲属性（能够减少受到的直接伤害）且行动费用较低，是突击的绝对主力；战斗机（Fighter）用于控制制空权，能够有效防止敌方轰炸机肆虐；轰炸机（Bomber）具备无伤打击地面目标的能力，但本体极其脆弱；火炮（Artillery）则能在安全的支援线后方直接轰击敌军前线，且不受敌方的战斗反击 1。  
为了丰富兵种特性，游戏引入了大量高频使用的关键字技能。例如，“闪击（Blitz）”允许单位在部署的当回合立刻进行移动或攻击；“守卫（Guard）”强制敌方单位必须优先攻击该目标，是保护核心单位与HQ的关键；“烟幕（Smokescreen）”使单位在主动行动前免疫任何指向性攻击与战斗伤害；“伏击（Ambush）”赋予单位在受击时先制反击的特权；而“狂怒（Fury）”则允许高阶单位在单回合内连续行动两次 1。这些关键字在标准卡组中的出场率极高，构成了卡牌强度的重要衡量标准。在卡组构成方面，指令卡（Order，即法术或事件卡）通常占据总卡组规模的百分之三十至四十，其单回合打出数量仅受限于玩家当前的指挥点余额。反制指令（Countermeasure）的引入则巧妙利用了玩家在回合结束时剩余的指挥点，使其能够在敌方回合触发，从而大幅增加了回合外的互动深度与心理博弈 6。  
关于卡组构筑，《Kards》采用了主次阵营（Main/Ally）的双国家规则。一个合法的对战卡组必须包含一个主阵营（最少二十八张卡，包含HQ）和一个盟友阵营（最多十二张卡） 7。这种设计使得卡组构建的组合基数呈指数级上升，极大丰富了游戏的环境（Meta）。同时，开发团队通过严格限制最高稀有度的精英卡（Elite）不得放入盟友阵营的卡槽中，有效地控制了强力单卡的泛滥，维持了底层平衡性 8。

### **2\. 国家阵营的不对称美学与平衡性变迁**

《Kards》中的七个主要国家阵营通过独特的卡牌机制高度绑定了其在二战中的历史定位，这种差异化的设计不仅增强了历史沉浸感，也为玩家提供了截然不同的战术体验。

| 国家阵营 | 历史军事定位 | 核心机制与标志性体系 | 版本平衡性历史表现与玩家反馈 |
| :---- | :---- | :---- | :---- |
| **美国 (USA)** | 工业巨头，后勤充沛，资源战 | 极其依赖跳费系统（Ramp），擅长前线占领，拥有大量高身材、高费用的终结级单位 2。 | 长期作为天梯最热门的次要盟友阵营（Ally），因其高效的跳费体系与泛用的过牌能力备受青睐 8。 |
| **德国 (Germany)** | 闪电战，精锐装甲突击 | 围绕闪击（Blitz）展开，辅以弃牌爆发机制、重甲坦克以及精锐的战术空军 2。 | 长期主导环境中的快攻（Aggro）流派，因低费闪击单位过于强大曾经历多次削弱，但仍稳居胜率榜首 3。 |
| **苏联 (Soviet Union)** | 消耗战，人力资源，严冬 | 标志性的轻步兵铺场（Light Infantry），以及大量通过自残HQ或友军换取超模身材的机制 2。 | 战术极度灵活，涵盖快攻铺场到后期严冬控制，其“自残增益”机制在天梯中常给对手带来极大压迫感。 |
| **大不列颠 (Britain)** | 海空防御，情报战，消耗 | 侧重于守护（Guard）、HQ回血机制、压制敌方行动（Pin机制），并拥有强大的航空母舰支援 2。 | 慢速控制流（Control）的绝对王者，但对新手极不友好，因其核心制胜手段多依赖难以获取的高稀有度卡牌 2。 |
| **日本 (Japan)** | 狂热进攻，玉碎战术，空优 | 强调摧毁增益（阵亡时触发效果）、直接伤害（Burn），甚至不惜自毁法力卡槽以换取短期极限爆发 2。 | 风格极端两极分化，抢血斩杀能力位居全阵营第一，但也极易因孤注一掷而面临资源枯竭的败局 3。 |
| **意大利 (Italy)** | 山地防线，辅助协同 | 独有的高山（Alpine）词条联动机制，随着场上同类单位增多而集体变强，辅以吸血回复 2。 | 作为附属阵营表现极其出色，顺风局滚雪球能力极强，但一旦丧失场面优势便极难在逆风中翻盘 2。 |
| **法国 (France)** | 抵抗组织，游击与破坏 | 围绕动员（Mobilize）机制成长，擅长手牌破坏、资源干扰以及抵抗运动系列事件卡 2。 | 机制相对晦涩且操作繁琐，干扰性极强，多被高级玩家用于针对特定环境的控制型套牌中 2。 |

### **3\. 商业变现与长线运营体系**

在商业化结构的搭建上，《Kards》采取了典型且经过市场验证的卡牌收集（CCG）模式。游戏内卡牌分为四个稀有度层级：基础（Standard，单卡组最多允许携带四张）、限制（Limited，最多三张）、特殊（Special，最多两张）以及精英（Elite，具有唯一性，仅限一张） 6。在盲盒销售方面，游戏设立了双轨制的卡包体系以满足不同消费层级的玩家。基础卡包售价一百金币，内含五张卡牌，并承诺保底出现一张限制级或更高稀有度的卡牌，这是新手玩家快速扩充基础卡池的主要途径 10。而面向中重度消费者的军官卡包则售价三百三十金币，内含七张卡牌，其保底机制大幅提升至至少包含一张特殊级与两张限制级卡牌，更为关键的是，军官卡包中掉落可兑换任意卡牌的万能卡（Wildcard）以及极其稀有的闪金卡（Gold Cards）的概率被显著放大 10。  
战令体系（Battle Pass）是其长线营收的重要支柱。该游戏采用了按月计费的订阅制定价模型，每月收费 11.99 美元 12。相较于一次性买断的战令，这种按月订阅的设计为活跃玩家提供了每日额外的任务槽、每日免费获取的单卡以及全局经验加成，对于维持极高粘性的核心玩家群体具有强大的吸引力 12。  
然而，该游戏在免费游玩（F2P）的友好度方面存在明显短板。入门级别的新手玩家若想解锁全卡图鉴几乎是一项不可能完成的任务。尽管每日任务能够提供相对稳定的金币产出，但环境中处于第一梯队（T1）的核心强力套牌（例如英国的深度控制流或德国的高阶装甲流）极度依赖多张难以获取的精英卡牌 2。数据与社区反馈显示，一名完全不付费的零氪玩家，通常需要经历三至四个月的高强度每日对局，才有可能通过积攒万能卡勉强构筑出两套具备天梯顶级竞争力的套牌 14。  
在内容迭代节奏上，开发团队保持着稳定的更新频率。通常每三个月进行一次包含数十张新卡的小型更新或重大平衡性调整，而每隔半年则会推出一次大型扩展包，引入约八十至一百张全新卡牌及附属的新机制词条（如“制空权”扩展包） 9。

### **4\. 市场数据表现与玩家口碑深度剖析**

自登陆 Steam 平台以来，《Kards》在同时在线数据上展现出了强大的生命力。其历史最高同时在线峰值（All-time Peak）达到了 8,966 人 17，而在近期的常态化运营中（2025至2026年区间），其日均最高在线人数稳健地维持在 2,500 至 3,000 人之间 19。在一个高度垂直且受众相对狭窄的二战军事CCG细分市场中，这一数据表现堪称优异，证明了其核心玩法的受众粘性。  
通过对超千条 Steam 玩家评价的词频与情感分析，可以清晰地勾勒出该作的口碑轮廓。正向评价的关键词高度集中于“对新手极其友好（Beginner-friendly）”、“绝佳的二战历史沉浸感（WWII stuff）”以及“高质量的美术与音效表现（Great art）” 20。而负面评价则尖锐地指出了游戏机制的底层痛点，主要集中在“令人窒息的后手劣势（Going second）” 21、“迫使玩家付费以保持竞争力（P2W）”以及“无脑堆砌低费单位（Light Infantry spam）” 15。  
深入剖析导致玩家流失的三大主因，首当其冲的是先后手平衡问题所带来的负面情绪。尽管开发团队曾公开服务器宏观数据，试图证明先手与后手的实际胜率差距在微观上不足百分之一 21，但在玩家的实际体感中，先手方往往能够依靠第一回合率先获得的行动点轻易占领并控制前线，随后引发的滚雪球效应（Snowball effect）使得后手玩家在整个对局中处于极度被动的挨打状态，这种“窒息感”导致了大量的挫败退坑 21。其次，环境中毒瘤卡组的存在严重破坏了对局体验。例如苏联阵营的“轻步兵无脑铺场”流派以及日本阵营的“无脑直伤打脸”卡组，使得缺乏深度战术交换、纯粹比拼手牌胡度的“自闭”对局增多，极大地剥夺了策略玩家的乐趣 15。最后，游戏内高频的表情系统常被部分玩家用于恶意嘲讽，社区内对于实装永久屏蔽全局表情功能的呼声极高，这种由互动恶意引发的社区氛围恶化也是不可忽视的流失因素 22。

### **5\. 系统借鉴清单与风险规避策略**

综合上述深度的系统拆解，在立项开发拿破仑主题CCG时，需严格遵循以下借鉴与规避清单。  
**必须全盘借鉴与吸收的优秀设计：**

1. 坚决保留操作点（Operation Cost）与部署点（Deployment Cost）的资源分离系统，这是模拟军事调度真实感的核心骨架。  
2. 延续主次阵营（28主+12次）的搭配规则，这在不增加开发成本的前提下，保证了游戏环境的多样性与自我平衡能力 7。  
3. 严格执行卡牌稀有度与单卡组携带数量上限挂钩的机制（尤其是精锐卡限带一张的设定），以此保证高端局内战术的不可预测性与卡牌的珍稀度价值 6。  
4. 继续采用基于真实历史兵种与战术的关键字包装手法（例如重甲单位附带减伤，战斗机具备制空拦截能力）。  
5. 维持公共前线或争夺区的设定，以此作为驱动玩家进行场面交换与强互动的核心空间 4。  
6. 引入万能卡（Wildcard）合成系统，彻底解决免费玩家无法定向获取核心卡牌的痛点，降低流失率 10。  
7. 坚持将指挥部（HQ）的存活与否直接绑定为游戏的唯一终结条件，使得战术目标始终清晰明确 1。  
8. 深入挖掘反制卡（Countermeasure）的设计，允许玩家利用回合结束时剩余的费用布置陷阱，大幅提升回合外的战略博弈感 6。  
9. 采用双轨制的消费结构（如基础包与军官包并行），有效拉开重度付费玩家与微氪玩家的消费梯度 10。  
10. 将所有的法术与环境结界卡牌统一包装为“军事指令卡（Orders）”，从UI到命名高度契合统帅部指挥主题 1。

**开发过程中必须坚决规避的设计陷阱：**

1. 必须打破完全镜像的线性费用增长模型，避免“先手必定率先占领优势阵地”。系统必须为后手玩家提供除了“额外抽取一张手牌”之外，更为实质且具影响力的反制补偿手段（例如起始自带护盾或专属的后手指令卡） 21。  
2. 严格杜绝产生无限套娃或零成本复制的衍生卡（如苏联轻步兵狂潮），必须在底层逻辑上对单回合内的召唤频率或铺场上限做出硬性限制 15。  
3. 避免设计出强度过高的纯直伤打脸卡组（Burn Deck），此类卡组会完全绕过前线争夺，剥夺游戏核心的场面交换乐趣。  
4. 避免任何单一国家阵营拥有全能的机制属性（例如既能跳费又能大量回复生命值），必须严格划分并锁定每个阵营的机制短板与软肋 2。  
5. 必须在MVP首发阶段即实装“默认全局静音与屏蔽表情”的选项，防患于未然，避免因互动恶意引发的早期口碑崩塌 22。

**有望实现超越的系统性弱点：**

1. 现有双线战场结构过于扁平，通过引入拿破仑战争的时代背景，可以构建具备更深战术纵深的三线战场。  
2. 缺乏复杂地形元素，若能引入“战场环境/阵地”光环卡，将极大提升博弈的维度。  
3. 单人PVE战役深度严重不足，本作完全可以利用拿破仑战史的史诗感，制作肉鸽化（Roguelike）的单机战役模式以吸引更广泛的受众。  
4. 原作受限于空战与坦克的强势，强行将海军边缘化，而本作可将特拉法加等宏大海战以特定的“战区增援”或“全局事件池”系统完美融入。  
5. 原作仅支持1v1对战模式。引入多方势力的2v2团队交战将直接切中历史模拟受众的巨大痛点，建立起难以逾越的品类差异化壁垒 23。

## ---

**二、 拿破仑时代设定的机制转化与历史考据**

为了精准击中PC端硬核策略游戏玩家群体对历史细节的考究癖好，势力设计与兵种分类必须在还原历史真实感与保障机制可玩性之间取得精妙的平衡。考据的最终目的不是撰写军事史论文，而是将其无缝转化为可落地的卡牌驱动机制。

### **1\. MVP 阶段定稿阵营与全景规划**

综合评估四周的MVP开发周期限制、美术资产工作量以及全球玩家的基础认知度，决定在首发阶段确立五个最具代表性的核心阵营，而将深受关注的西班牙（及其独特的游击战机制）保留为1.0版本之后的首个大型DLC内容 25。

| 势力名称 | 阵营机制一句话定位 | 标志性统帅与将领 | 关键战役与史诗事件卡 | 核心兵种序列群 |
| :---- | :---- | :---- | :---- | :---- |
| **法兰西第一帝国** | 狂暴攻坚：依靠极具威慑力的纵队冲锋与老近卫军的压倒性面板，强行获取场面的绝对优势。 | 拿破仑·波拿巴、米歇尔·内伊、路易·达武 | 奥斯特里茨的艳阳、老近卫军出击、颁发荣誉军团勋章 | 猎兵/散兵连（Voltigeurs）、老近卫军、胸甲骑兵（Cuirassiers）、近卫马炮兵 27。 |
| **大不列颠及爱尔兰联合王国** | 绝对防御与制海：依托坚如磐石的红衣线列步兵防守反击，通过高费海军指令卡从外部控制战局资源。 | 惠灵顿公爵、霍雷肖·纳尔逊、托马斯·皮克顿 | 特拉法加海战、托雷斯韦德拉斯防线、威灵顿的防冻靴 | 红衣线列步兵、绿夹克步枪手（95th Rifles）、苏格兰高地步兵、皇家重骑兵、一级战列舰 28。 |
| **俄罗斯帝国** | 资源消耗与极端气候：拥有极高的基地血量，擅长利用焦土政策与严寒天气卡牌持续削弱全场单位。 | 米哈伊尔·库图佐夫、彼得·巴格拉季昂、马特维·普拉托夫 | 莫斯科焦土政策、俄罗斯的严冬、1812序曲 | 东正教民兵（Opolchenie）、顿河哥萨克轻骑兵、巴甫洛夫斯克掷弹兵、独角兽榴弹炮 30。 |
| **普鲁士王国** | 军事改革与全面动员：极致的快速过牌与低费铺场，依靠大量国民军与高机动轻骑兵发起闪电突袭。 | 格布哈德·布吕歇尔、奥古斯特·格奈森瑙、格哈德·沙恩霍斯特 | 前进，孩子们！、铁十字勋章的诞生、莱比锡民族大会战 | 西里西亚国民军（Landwehr）、黑色布伦瑞克军、死骑兵（骷髅骠骑兵，Totenkopf Hussars） 32。 |
| **奥地利帝国** | 战术协同与多民族联盟：拥有类别最为繁多的兵种，当场上同时存在不同类别的部队时，触发强力的联合光环增益。 | 卡尔大公、卡尔·菲利普·施瓦岑贝格 | 阿斯珀恩-埃斯灵大捷、帝国大动员、白色方阵的坚韧 | 白色线列步兵、匈牙利掷弹兵、边防军（Grenzer）、乌兰枪骑兵（Uhlans） 34。 |

注：波兰/莱茵邦联等仆从国将作为法军的附属卡牌（Ally）出现，不独立成军 36；奥斯曼帝国由于机制差异过大（如禁卫军Janissaries体系），暂不纳入前期规划 37。

### **2\. 历史考据要点向卡牌机制的深度映射**

拿破仑战争在战术层面上的核心精髓在于“多兵种协同作战（Combined Arms）”以及步、骑、炮之间形成的“三维相克”动态博弈 27。这些历史真实的战术细节必须被精准地提炼为游戏内的词条（Keywords）。  
交战方式的数字化转化是设计的重中之重。在历史中，步兵的阵型决定了其战斗效能。因此，处于“线列（Line）”状态的步兵单位将获得【齐射】词条，使其在发起攻击前能先行造成基于自身攻击力一半的先制伤害，模拟大兵团齐射的压制力 27。处于“纵队（Column）”状态的单位，因其具备极强的冲击动能，将获得【突破】词条（溢出的伤害将直接打击敌方指挥部），但作为代价，其更容易成为火炮的靶子，防御力需减免。而“散兵（Skirmisher）”单位则通过分散站位获得【掩护】词条，使其在遭受非火炮类攻击时免疫第一击的伤害 27。  
关于海战系统的处理，调研结论明确指出，不应在MVP阶段设置独立的海战面板，因为这极易导致战局重心的割裂感。相反，海军力量应当被巧妙地融入主战场体系中。海军单位可作为部署在支援区极后方的“不可移动实体”，或是转化为高费用的“战术指令卡”。例如，【皇家海军舰炮支援】可以设定为一张高费清场法术，直接抹平敌方后排的脆弱火力点。诸如特拉法加海战或尼罗河战役，则作为英国阵营专用的终极史诗事件卡存在，为战局带来扭转乾坤的效果。  
后勤、士气、天气等“软系统”的硬化处理同样关键。士气（Morale）不宜作为复杂的次级经济资源增加玩家的算力负担，而是转化为单位的状态增益或减益（BUFF/DEBUFF）。例如，被施加【溃散】状态的单位将丧失下一回合的行动权；而处于【高昂】状态的骑兵则获得额外的攻击力加成。天气系统（如代表泥泞或大雪的天气卡）则被设定为全局结界卡，打出后能够持续改变战场的规则两到三个回合，深度契合俄罗斯阵营的消耗战术。

### **3\. 历史敏感性与规避原则**

在面向全球（尤其是欧美主流市场）发行时，必须妥善处理历史争议。整体原则是**去政治化处理**，全盘采用真实的历史势力名称与人物名讳。在当今市场认知中，拿破仑战争已被高度“游戏化”和“浪漫化”，不存在不可逾越的政治红线。  
但在特定领域必须进行模糊化处理以规避舆论风险。开发团队应彻底避开海地革命以及拿破仑恢复奴隶制的相关政策，这是现代欧美文化极度敏感的红线区域。对于西班牙半岛战争中发生的残酷暴行和血腥镇压，美术表现上绝不使用写实的血腥处决插画。取而代之的，是采用类似西班牙著名画家弗朗西斯科·戈雅（Goya）在其不朽名作《战争的灾难》（Disasters of War）中所使用的蚀刻版画风格，通过**抽象的黑色剪影与极具张力的线条**来传达“焦土”或“游击战”的残酷氛围，以此巧妙规避游戏年龄分级的严格审查。

## ---

**三、 核心机制设计的突破与重构**

本章节所确立的底层机制，决定了本作能否摆脱对竞品的简单模仿，从而确立在拿破仑战棋领域中唯一的爆款CCG地位。

### **1\. 行动点系统的拿战化包装与改良**

在基础资源的命名上，经过严密评估，推荐使用\*\*“军令（Orders）”\*\*作为行动点系统的官方名称。这一命名最为契合近代军队统帅部的指挥逻辑与军事文化。  
在曲线的改造上，虽然直接套用竞品《Kards》线性的自然增长曲线（每回合增加一点，上限十二点）能够最大程度地降低新玩家的学习门槛，但为了凸显拿破仑战争的战术深度，必须在进阶规则中对“军令”系统进行革命性的拆分。**军令（Orders）资源池将被划分为两个独立的微循环：**

* **征召点（Muster）**：专门用于将单位卡牌从手牌部署至后方的支援线。  
* **指令点（Command）**：专门用于驱使已经处于场上的单位进行开火、移动或变换阵型（如结成方阵）。  
  在机制的改良运作中，玩家每回合获得的总费用依然由回合数决定，但系统赋予玩家极大的自由度，允许其在每个回合开始时，自行决定将总费用以何种比例投入“征召”池与“指令”池中。这种弹性资源的分配设计，完美模拟了历史上的军队统帅在“呼叫后方增援”与“对前线部队进行微操指挥”之间所面临的痛苦抉择，极大地拔高了游戏的策略天花板。

### **2\. 战场结构的维度升级**

**明确推荐：采用方案 B，即“三线纵深结构”。**  
完全复用《Kards》的双线结构（前线与支援线）过于扁平且过度抽象，根本无法容纳拿破仑战术体系中处于绝对核心地位的兵种——炮兵。历史数据显示，拿破仑战争中高达百分之五十的伤亡是由火炮造成的，而火炮通常部署在战线的最后方，受到前方步兵的严密保护 27。因此，三线结构是唯一合理的选择。其原型流程构建如下：

1. **后卫线（Rear Guard）**：即指挥部（HQ）所在地。炮兵阵地和补给车辆只能部署于此区域。火炮极其脆弱，但能够跨越战线对远距离目标实施毁灭性打击。  
2. **主力战列线（Line of Battle）**：玩家打出步兵和重骑兵时的默认集结区域，也是构筑坚固防线的核心地带。  
3. **争夺区 / 散兵线（No Man's Land）**：位于双方主力战列线之间的公共区域（设定容量为四个单位）。只有将步兵单位推进并占据此区域，才能对敌方的主力战列线发起有效攻击；同时，高机动的轻骑兵可以利用该区域作为跳板，直接向敌方后卫线的炮兵阵地发起致命冲锋 27。

这种三线结构的设计在上手门槛上仅略高于双线模式，但其带来的战术纵深感呈现指数级增长，完美容纳并复现了拿破仑战争真实的地貌特征与交战距离。

### **3\. 多势力对战的可行性与核心决策**

在MVP阶段是否引入多方对战机制，是本项目面临的最大风险决策点。  
通过对过往失败案例的深度调研发现，如《Artifact》和《Hex》等试图在数字CCG中实现复杂多线或多维博弈的作品，其失败的根本原因在于战线设计过于冗长（单局耗时常达三十至四十五分钟）、玩家心智负担过重，以及经济模型失衡导致入坑成本极高 39。如果在数字CCG中引入三人或四人的无限制混战（Free-for-all），必然会陷入“两方弱势结盟共同针对一方优势”的极度负面体验怪圈。桌游如《Diplomacy》（外交）中依赖玩家之间“口头谈判与背叛”的嘴炮机制，是无法通过冰冷的代码机制在数字游戏中完美还原的。  
然而，2v2团队战模式却在卡牌领域有着极其成功的范本——《万智牌（MTG）》的“双头巨人（Two-Headed Giant）”模式 23。其成功的核心机制在于：两名队友共享生命值（即HQ血量叠加为庞大的单体），共享回合的各个阶段，并在同一时序内同步行动；但双方的卡组和手牌完全独立，且不能跨越权限使用自己的资源去替队友打出卡牌 23。  
拿破仑战争的历史本质，就是一部“反法同盟联军对抗法兰西帝国”的宏大史诗。2v2模式（例如一名玩家操控英国加上另一名操控普鲁士，共同对抗两名操控法国及仆从国的玩家）带来了无与伦比的代入感与极高的社交传播价值。  
**最终推荐方案：方案 B。MVP 版本必须包含 2v2 团队战模式，但坚决不做无序混战。** 在MVP落地实施时，系统将实装1v1天梯排位与2v2休闲匹配。2v2战场的开发成本可通过复用资源来控制，只需将双方HQ的血量上限提升至四十点，拓宽公共散兵线的容量即可。其所带来的营销噱头与社交裂变能力，将是本作的杀手锏。

### **4\. 兵种克制矩阵的历史逻辑转换**

优秀的卡牌游戏最忌讳让玩家死记硬背枯燥的克制数值。基于拿破仑时代的战术准则 27，兵种之间的克制关系必须通过极其直观的**词条（Keywords）特性**自然地发生作用。

| 攻击发起方 | 目标承受方 | 历史底层逻辑设定 | 游戏机制转化表现 |
| :---- | :---- | :---- | :---- |
| **重骑兵** (胸甲骑兵) | **线列步兵 / 散兵** | 在开阔平原上，重骑兵的冲锋能够轻易冲垮未能及时结成密集阵型的步兵阵列 27。 | 当攻击未处于“方阵”状态的步兵单位时，造成双倍伤害，并必定附带“突破（Smash）”效果穿透至HQ。 |
| **方阵步兵** (Square) | **所有骑兵兵种** | 步兵结成的密集刺刀丛林，会让冲锋的战马出于动物本能拒绝冲撞，从而瓦解骑兵攻势 27。 | 步兵获得专属技能【结阵】：主动消耗1点军令变换形态。结阵后防御力永久+4，所有骑兵对其发起的攻击伤害减半，且骑兵将承受步兵反击的全额伤害。 |
| **重炮兵** (12磅野战炮) | **方阵步兵 / 纵队** | 实心圆形炮弹（Round Shot）会在密集的步兵阵列中引发致命的跳弹效应，像保龄球一样造成一条直线上的惨重伤亡 27。 | 当火炮攻击具有“方阵”或“密集纵队”状态的单位时，造成 2 倍甚至 3 倍的毁灭性溅射伤害。 |
| **轻骑兵** (骠骑兵/哥萨克) | **后方炮兵阵地** | 高机动轻骑兵能够利用速度优势穿透敌方防线盲区，突入后方并用长钉封死火炮的引火孔（Spiking the guns）使其报废 27。 | 获得【侧翼迂回】词条，当散兵线有空位时，可无视主力战列线的嘲讽，直接跨线攻击敌方后卫线的炮兵，并必定秒杀无防备的火炮。 |

## ---

**四、 PC 端竞品生态与平台发行战略**

### **1\. Steam 平台 CCG 现状的残酷真相**

在2024至2025年的市场数据中，Steam 平台上的独立游戏生存环境极度恶劣。全年发布的新游戏数量超过一万八千款，但能够取得商业成功的项目（以突破1000条评价为基准）比例不足百分之三 43。数字CCG市场更是呈现出严重的寡头化趋势，头部流量被《Marvel Snap》（依靠移动端爆发反哺PC）以及《Yu-Gi-Oh\! Master Duel》（依托长达二十年的实体卡牌IP背书）所绝对垄断 45。  
处于中型体量梯队的《Kards》能够屹立不倒，维持近 3000 的高粘性日活 19，其核心秘诀在于“精准且不可替代的二战历史军事定位”。反观《Artifact》与《Hex》等具备顶级大厂背景的作品，却因机制过度复杂、单局耗时过长以及经济模型劝退而迅速暴死 40。  
核心结论昭然若揭：**在当前的PC端市场，缺乏超级IP背书的纯架空设定CCG几乎注定失败，本作必须依托极强的“历史军事题材壁垒”来吸引受众。** 拿破仑题材在庞大的硬核策略玩家群体（例如《全面战争：拿破仑》的数百万累计受众）中，具有着无可比拟的天然吸量能力与忠诚度。

### **2\. 聚焦 PC 端的绝对差异化竞争优势**

在MVP阶段果断放弃对移动端的适配，是一次极具前瞻性的战略收缩。PC 端CCG具备手游无法企及的独占优势：

* **极致的信息密度与宏大叙事呈现**：移动端狭小的屏幕根本无法展示三线战场的宏伟感。PC 端的高分辨率大宽屏允许同屏清晰展示 15 到 20 个单位，外加各种天气特效，能够完美复现拿破仑战争“千军万马会战”的史诗感。  
* **深不可测的 Mod 社区潜力**：游戏将全面对接 Steam 创意工坊（Steam Workshop）。允许玩家利用内置编辑器自定义历史战役残局（Puzzle）并上传分享（借鉴《杀戮尖塔》的成功经验），这种UGC（用户生成内容）生态在延长游戏寿命的长尾效应上是无敌的。  
* **过滤快餐玩家，沉淀硬核受众**：PC 玩家群体更具备沉浸耐心，能够容忍 15 至 20 分钟的中局时长，并且对粗暴的“充钱变强（Pay-to-Win）”极度敏感，更倾向于享受深度的牌组构筑与逻辑验证过程。

### **3\. Steam 发行策略的选择**

**强烈推荐：采用抢先体验（Early Access，EA）发行模式。**  
任何卡牌游戏的数值平衡都不可能仅仅依靠内部数十人的 QA 团队来完善，必须将两百五十张首发卡牌的平衡性交给数万名 EA 玩家进行高强度、穷举式的验证。闭门造车强推 1.0 正式版是 CCG 开发的致命大忌。同时，在 EA 发行前，必须充分利用 Steam 新品节（Next Fest）的巨大流量红利推出 Demo 试玩版。根据近期市场数据剖析，参展新品节的独立游戏，其愿望单转化率通常是日常自然增长的五倍以上。

## ---

**五、 美术风格定位与视觉管线**

拿破仑战争题材在视觉传达上面临着两难的困境：若采用过度写实的传统油画风格，不仅会导致游戏画面显得沉闷压抑，其庞大的高精度资产制作成本也会拖垮整个项目；而若采用过度低幼的卡通风格，则会瞬间劝退那些最核心、对历史细节极其挑剔的考究党玩家。

### **1\. 美术风格确立：新古典构图下的“海报化漫画风”**

明确推荐方案：选择方案 B（海报化漫画风），并以此为基底深度融合雅克-路易·大卫（Jacques-Louis David）等同时代画巨匠的英雄主义构图 47。  
在视觉对标上，本作将吸取《Kards》式的高对比度复古军政海报色彩风格 1，但在人物边缘及轮廓的处理上，大胆加入类似欧美成人硬派漫画的粗黑线勾勒。这种风格在 2D 卡面上具备极高的辨识度，且制作管线极为成熟。在当前的生产力条件下，团队能够利用 AI 技术基于线稿快速生成底图并进行大批量的人工精修与上色，从而在 MVP 阶段以不可思议的效率大幅压低美术外包成本。  
色彩心理学将被深度应用于阵营区分。法国的法兰西蓝与耀眼金色、英国的醒目龙虾红、普鲁士的铁十字黑与银色、俄罗斯的深邃墨绿与雪白、奥地利的纯白底色，这些极具代表性的色彩将构成战场的视觉底色，形成极其强烈的阵营对立感。

### **2\. 卡面 UI 的档案化布局逻辑**

彻底摒弃传统如《炉石传说》式的椭圆包裹边框，转而采用极具时代感的\*\*“军事机密档案”或“羊皮纸令状”\*\*式的卡面UI设计：

* **数值分布**：摒弃花哨复杂的图标，采取最直白硬朗的排版。左上角显示“军令消耗”（采用类似暗红色火漆印章的视觉设计），左下角显示攻击力（两把交叉的燧发枪图标），右下角显示防御力/血量（坚固的盾牌或闪亮的胸甲图标）。  
* **兵种标识体系**：在卡牌正上方中心位置，直接使用北约军事符号体系的复古变体（例如：矩形框中加上单斜线代表骑兵，加上巨大的交叉X代表步兵）直接标明兵种分类。这种设计能让资深军迷一眼看懂，极大降低认知成本。  
* **异画卡（Foil）的独特设计**：对于高稀有度精英卡的闪卡特效，坚决摒弃廉价的彩色炫光动画。将其设计为一种“历经沧桑的褪色旧黑白照片，随着出场动画瞬间焕发为全彩油画”的动态过渡效果，拉满史诗感。

## ---

**六、 商业化变现与首发节奏规划**

在极度内卷的 Steam 生态池中谋求生存，商业化设计绝不仅仅是单纯的盈利收割手段，它更是筛选用户、调节生态和控制留存漏斗的核心工具。

### **1\. 定价模型底座：F2P 驱动 \+ 创始人包 \+ 战令订阅**

**明确结论：必须采取免费游玩（F2P）模式作为驱动装机量的绝对核心。**  
基于近期对 Steam 市场的洞察，诸如《Path of Exile 2》早期测试以及《The Bazaar》等案例的经验深刻表明，买断制（Buy-to-Play）的 CCG 极其难以维持长线且健康的天梯匹配池 50。Steam 玩家群体对于本质上是 F2P 内核（存在内购抽卡）却强行售卖入场门票的行为表现出极度的厌恶与抵触，因此游戏本体必须坚持完全免费下载。  
**创始人包（Founder's Pack）的营销策略**：建议定价为 29.99 美元（国区约合 149 元人民币） 52。创始人包内应包含绝版专属的拿破仑或惠灵顿异画主战者动态头像、专属的黄金桂冠卡背、二十个高爆率的军官卡包以及首发赛季的豪华战令 53。核心原则是：绝不在包内出售任何具有独占数值优势的卡牌，仅仅售卖极度稀缺的视觉荣誉与进度加速器，以规避 P2W 的差评风暴。  
**底层经济循环**：仿照《Kards》经过验证的机制，开包过程中将掉落万能卡（Wildcards），用于无限制合成指定的卡牌 10。系统必须通过精密的数值演算，确保一名保持正常活跃度的免费玩家，每周能够通过积累合出至少一到两张核心的紫卡或金卡，从而保障零氪玩家的生存体验。

### **2\. 首发内容体量与卡池刻度**

* **核心参战阵营**：五个（法兰西、大不列颠、俄罗斯、普鲁士、奥地利）。  
* **卡池规模控制**：MVP 版本严格控制在 **240 张卡牌**。具体构成逻辑为：每个核心阵营拥有 40 张专属卡，外加 40 张所有阵营均可调用的通用中立卡（例如雇佣兵、天气变化卡、通用战场事件）。单阵营 40 张的内部稀有度构成为：20张基础卡 \+ 10张限制卡 \+ 6张特殊卡 \+ 4张精英卡。这个精准的体量既不会导致开发周期失控，也足以在首发阶段支撑起至少三十种截然不同的主流构筑套路。

### **3\. 史诗赛季更迭节奏**

以“宏大的历史战役”为推进轴线，规划每三个月为一个完整赛季：

* **S1 赛季：太阳的奥斯特里茨**（本体首发，奠定三皇会战的基调）。  
* **S2 赛季：半岛的无尽血战**（新增西班牙阵营的 40 张卡牌，全面引入游击战与地形袭扰体系） 25。  
* **S3 赛季：冰雪狂想曲**（以俄罗斯战场为主体，引入极深度的动态天气气候机制）。  
* **S4 赛季：怒海争锋**（作为首个超大型 DLC，正式将海军独立战术与海战事件包推向高潮）。

## ---

**七、 底层技术选型与团队建制**

### **1\. 引擎与底层技术栈决策**

**强烈建议：全面拥抱 Godot 4.x 引擎。** 在过去，Unity 一直是 CCG 开发的默认主流。然而，相较于 Unity 近年来因收费策略变更所引发的严重开发者信任危机，以及其底层架构日益增加的臃肿感，Godot 引擎在处理 2D、UI 密集型交互游戏（正如 CCG 品类）上的性能表现极其轻量且优越 54。Godot 独树一帜的节点系统（Node System）在逻辑上天然契合卡牌游戏中实体组件层层嵌套的复杂结构，能够极大加快原型的迭代速度 55。  
**网络同步架构**：卡牌游戏对于网络延迟（Ping值）具有极高的宽容度，但对底层逻辑校验的严谨性要求却达到极致。项目将采用自建专用服务器（Dedicated Server）架构。核心的战斗规则、抽卡概率与伤害演算完全以服务器权威（Server-Authoritative）模式运行，客户端退化为仅负责播放华丽动画与发送玩家基础指令的“播放器”。  
**反作弊机制**：得益于服务器权威的架构，本机内存中根本不存在敌方未打出的手牌数据，这从物理层面上彻底杜绝了“透视手牌”等恶性外挂的可能。因此，本作完全不需要接入 EAC 等会导致性能拖累的重型反作弊中间件。

### **2\. 人力资源规划与敏捷估算**

为了在极其苛刻的 4 周时间内交付高质量的 MVP 核心战斗原型，需要组建一支编制精简但执行力极强的突击小队（总计约 10-12 人）：

* **制作人兼主策划（1人）**：拥有绝对的机制决定权，统筹大局并独立撰写首发 240 张卡牌的详细数值与底层机制白皮书。  
* **程序攻城狮（3人）**：1名专攻 Godot 前端交互与 UI 动效表现；1名负责后端逻辑、数据库与匹配服务器的搭建；1名专注于战斗状态机与核心结算算法的编写。  
* **美术资产组（3-4人）**：1名主美负责把控整体视觉基调，统筹 AI 辅助线稿与外包上色管线；1名 UI/UX 专家打磨卡面与交互面板；1名动效师负责华丽的卡牌入场与全屏法术特效。  
* **QA 测试工程师（1-2人）**：在 CCG 开发中，人工测试效率极低，QA 必须具备编写自动化测试脚本的能力，让 AI 进行数万次的逻辑穷举以排除卡牌词条互动引发的恶性 Bug。

## ---

**八、 关键决策答疑清单**

针对项目启动前必须明确的核心疑问，以下提供毫无歧义的最终执行定论，绝不含糊其辞：

1. **多方对战 MVP 是否纳入？**  
   * **明确结论：坚决纳入，严格执行方案 B。** MVP 必须首发包含 2v2 团队匹配战（盟军对抗法军）。这一决定直击传统 CCG 长期以来社交性羸弱的致命死穴，且基于共享生命值的“双头巨人”联机机制在底层开发层面上，远比逻辑极度混乱的多人自由混战要可控得多。  
2. **战场结构选哪个？**  
   * **明确结论：采用三线纵深结构（后卫炮兵线 / 主力战列线 / 公共散兵争夺线）。** 这一设计完美映射了拿破仑时代火炮至上的兵种交战距离，从根本上解决了对标竞品《Kards》纵深感严重不足的体验短板。  
3. **美术风格定哪种？**  
   * **明确结论：海报化硬派漫画风。** 在高对比度的复古军事海报调色基底上，结合十九世纪新古典主义的悲壮英雄构图。此举既死死拿捏了历史的庄重感，又借助漫画式的线条极大降低了资产的批量生产门槛。  
4. **历史人物 \+ 真实势力名，还是半架空？**  
   * **明确结论：必须使用真实历史人物与真实势力本名。** 在欧美成熟的受众市场中，拿破仑战争早已脱离政治敏感的泥潭。只需巧妙规避如大规模平民处决、奴隶制等反人类暴行即可，其余细节必须保持绝对的“历史原汁原味”，这是撬动硬核玩家钱包的唯一密钥。  
5. **F2P 还是买断？**  
   * **明确结论：F2P（免费游玩核心）+ 高附加值创始人包 \+ 战令内购。** 铁血的市场数据表明，在 Steam 强推纯 PVP 卡牌游戏的买断制等同于商业自杀，唯有免费的低门槛才能引流并撑起天梯匹配池所需的庞大活水基数。  
6. **首发包含几个阵营？**  
   * **明确结论：首发锁定 5 个核心阵营。** 即法兰西、大不列颠、俄罗斯、普鲁士与奥地利。西班牙的游击战线将作为 1.0 上线后的首个重磅资料片独立发布。  
7. **海战是否进入 MVP？**  
   * **明确结论：不作为独立的战场模块进入 MVP。** 强行在陆战主轴旁并列加入海战面板会导致底层逻辑与玩家注意力的灾难性割裂。在 MVP 阶段，海战以英国等特定势力的“超级指令卡”（如毁天灭地的【特拉法加舷侧齐射】）形式，震撼降临于主战场体系内。  
8. **Early Access 还是 1.0？**  
   * **明确结论：采用 Early Access（抢先体验）发行。** 游戏必须利用狂热的先锋玩家社区，进行长达数月的高强度数值平衡与环境（Meta）迭代验证。卡牌游戏企图闭门造车、一步到位发布 1.0 正式版，是业内最大的傲慢与忌讳。

### ---

**九、 系统风险评估与立项最终结论**

**系统性风险清单（NO-GO 隐患排查）**：

1. **先手优势的滚雪球崩塌风险**：拿破仑战争高度依赖阵地的排布与抢占，若先手玩家能够无脑向前推衍散兵线形成绝对压制，本作必将重蹈《Kards》因后手体验极差而导致玩家大规模流失的覆辙。研发团队必须在底层机制上，为后手玩家的第一回合强行注入诸如“初始地形掩体加成”等破局手段。  
2. **2v2 模式的网络同步灾难**：在传统的 P2P 联机架构下，四人局的掉线率呈指数级上升。技术团队必须立下军令状，确保专用服务器能够提供无缝断线重连的极致稳定性。

**立项最终评估结论：STRONG GO（强烈建议立即立项）。**  
在当前竞品极度稀缺的 PC 端垂直历史题材领域，本项目稳稳踩在了《Kards》已被市场反复验证成功的二战机制地基之上，并大胆注入了拿破仑战争的强历史浪漫主义色彩与前所未有的 2v2 团队战役创新。在核心战斗底层上，通过利用“方阵、线列、火炮”构成的直观历史克制链，完美解决了硬核玩家对冷热兵器过渡时代战术模拟的长期痛点。鉴于该 MVP 方案商业化路径极其清晰、选用引擎技术栈成熟轻量，展现出了极具爆发力的突围潜力，建议立刻抽调精英资源，于下周正式启动为期四周的 MVP 核心原型突击开发。

#### **Works cited**

1. How to play | KARDS: The WWII Card Game, accessed May 4, 2026, [https://www.kards.com/how-to-play](https://www.kards.com/how-to-play)  
2. Can someone explain the factions and their play style? : r/kards \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/kards/comments/1h1kc68/can\_someone\_explain\_the\_factions\_and\_their\_play/](https://www.reddit.com/r/kards/comments/1h1kc68/can_someone_explain_the_factions_and_their_play/)  
3. Nations general strategies :: KARDS \- The WWII Card Game General Discussions, accessed May 4, 2026, [https://steamcommunity.com/app/544810/discussions/0/2763442118823754382/](https://steamcommunity.com/app/544810/discussions/0/2763442118823754382/)  
4. Battlefield elements: The Frontline \- Kards Support, accessed May 4, 2026, [https://support.kards.com/hc/en-us/articles/360026464712-Battlefield-elements-The-Frontline](https://support.kards.com/hc/en-us/articles/360026464712-Battlefield-elements-The-Frontline)  
5. Guides and general mechanics \- Kards Support, accessed May 4, 2026, [https://support.kards.com/hc/en-us/sections/360004083012-Guides-and-general-mechanics](https://support.kards.com/hc/en-us/sections/360004083012-Guides-and-general-mechanics)  
6. Card rarity \- Kards Support, accessed May 4, 2026, [https://support.kards.com/hc/en-us/articles/360026768151-Cards](https://support.kards.com/hc/en-us/articles/360026768151-Cards)  
7. Nations \- Kards Support, accessed May 4, 2026, [https://support.kards.com/hc/en-us/articles/360026461872-Nations](https://support.kards.com/hc/en-us/articles/360026461872-Nations)  
8. KARDS \- The WWII Card Game :: Let there be Data\! \- Steam Community, accessed May 4, 2026, [https://steamcommunity.com/games/544810/announcements/detail/2975125100805333957](https://steamcommunity.com/games/544810/announcements/detail/2975125100805333957)  
9. Air Supremacy: Full Card Overview | KARDS: The WWII Card Game, accessed May 4, 2026, [https://www.kards.com/news/air-supremacy-full-card-overview](https://www.kards.com/news/air-supremacy-full-card-overview)  
10. Shop: Purchasing card packs with Gold – Kards Support, accessed May 4, 2026, [https://support.kards.com/hc/en-us/articles/360027377612-Shop-Purchasing-card-packs-with-Gold](https://support.kards.com/hc/en-us/articles/360027377612-Shop-Purchasing-card-packs-with-Gold)  
11. Gold Cards \- Kards Support, accessed May 4, 2026, [https://support.kards.com/hc/en-us/articles/360027672711-Gold-Cards](https://support.kards.com/hc/en-us/articles/360027672711-Gold-Cards)  
12. The KARDS Battle Pass \- The WWII Card Game, accessed May 4, 2026, [https://www.kards.com/news/the-kards-battle-pass](https://www.kards.com/news/the-kards-battle-pass)  
13. New player are battle passes worth the purchase? : r/kards \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/kards/comments/1h2nvn4/new\_player\_are\_battle\_passes\_worth\_the\_purchase/](https://www.reddit.com/r/kards/comments/1h2nvn4/new_player_are_battle_passes_worth_the_purchase/)  
14. Is this pack worth buying? : r/kards \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/kards/comments/1hpfoe3/is\_this\_pack\_worth\_buying/](https://www.reddit.com/r/kards/comments/1hpfoe3/is_this_pack_worth_buying/)  
15. New (thrilled but also upset) player here : r/kards \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/kards/comments/1ay05ut/new\_thrilled\_but\_also\_upset\_player\_here/](https://www.reddit.com/r/kards/comments/1ay05ut/new_thrilled_but_also_upset_player_here/)  
16. Chances to get rarities in packs? : r/kards \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/kards/comments/13z1acv/chances\_to\_get\_rarities\_in\_packs/](https://www.reddit.com/r/kards/comments/13z1acv/chances_to_get_rarities_in_packs/)  
17. Most played Board Game Games Steam Charts \- SteamDB, accessed May 4, 2026, [https://steamdb.info/charts/?tagid=1770](https://steamdb.info/charts/?tagid=1770)  
18. Steam charts \- The WWII Card Game · KARDS \- SteamDB, accessed May 4, 2026, [https://steamdb.info/app/544810/charts/](https://steamdb.info/app/544810/charts/)  
19. The WW2 Card Game \- KARDS \- Steam Charts, accessed May 4, 2026, [https://steamcharts.com/app/544810](https://steamcharts.com/app/544810)  
20. KARDS user reviews \- Metacritic, accessed May 4, 2026, [https://www.metacritic.com/game/kards/user-reviews/](https://www.metacritic.com/game/kards/user-reviews/)  
21. Feedback from frustrated player :: KARDS \- The WWII Card Game General Discussions, accessed May 4, 2026, [https://steamcommunity.com/app/544810/discussions/0/595142234675945416/](https://steamcommunity.com/app/544810/discussions/0/595142234675945416/)  
22. Cool card game, garbage playerbase :: KARDS \- The WWII Card Game General Discussions \- Steam Community, accessed May 4, 2026, [https://steamcommunity.com/app/544810/discussions/0/595159120097764779/](https://steamcommunity.com/app/544810/discussions/0/595159120097764779/)  
23. Two-Headed Giant \- Pastimes Events, accessed May 4, 2026, [https://www.pastimesevents.com/two-headed-giant/](https://www.pastimesevents.com/two-headed-giant/)  
24. MTG Two-Headed Giant \- Magic: The Gathering \- Wizards of the Coast, accessed May 4, 2026, [https://magic.wizards.com/en/formats/two-headed-giant](https://magic.wizards.com/en/formats/two-headed-giant)  
25. Spanish Army (Peninsular War) \- Wikipedia, accessed May 4, 2026, [https://en.wikipedia.org/wiki/Spanish\_Army\_(Peninsular\_War)](https://en.wikipedia.org/wiki/Spanish_Army_\(Peninsular_War\))  
26. Napoleonic Spanish Army Sheet (1807-1814) | PDF | Cavalry | Infantry \- Scribd, accessed May 4, 2026, [https://www.scribd.com/document/731130979/Valour-and-Fortitude-Napoleonic-Spanish-Army-Sheet-v1-21](https://www.scribd.com/document/731130979/Valour-and-Fortitude-Napoleonic-Spanish-Army-Sheet-v1-21)  
27. Napoleonic tactics \- Wikipedia, accessed May 4, 2026, [https://en.wikipedia.org/wiki/Napoleonic\_tactics](https://en.wikipedia.org/wiki/Napoleonic_tactics)  
28. Napoleon at War V1 & Army Lists | PDF \- Scribd, accessed May 4, 2026, [https://www.scribd.com/document/392313965/Napoleon-at-War-V1-Army-Lists](https://www.scribd.com/document/392313965/Napoleon-at-War-V1-Army-Lists)  
29. British Regiments in the Peninsular War 1808-1814 \- The Napoleon Series, accessed May 4, 2026, [https://www.napoleon-series.org/military-info/organization/Britain/Strength/c\_RegimentsinPeninsula.html](https://www.napoleon-series.org/military-info/organization/Britain/Strength/c_RegimentsinPeninsula.html)  
30. Napoleonic Russians \- von Peter himself, accessed May 4, 2026, [http://vonpeterhimself.com/army-inspections/napoleonic-russians.html](http://vonpeterhimself.com/army-inspections/napoleonic-russians.html)  
31. The Napoleonic Wars \- Boardgame Players Association, accessed May 4, 2026, [http://www.boardgamers.org/specific/nappy.htm](http://www.boardgamers.org/specific/nappy.htm)  
32. Prussian Army Resources | Befreiungskriege 1813-14 \- WordPress.com, accessed May 4, 2026, [https://befreiungskriege.wordpress.com/prussian-army-resources/](https://befreiungskriege.wordpress.com/prussian-army-resources/)  
33. Prussian Army of the Napoleonic Wars : History : Organization : Generals, accessed May 4, 2026, [http://napoleonistyka.atspace.com/Prussian\_army.htm](http://napoleonistyka.atspace.com/Prussian_army.htm)  
34. 'Imperial & Royal': My 15mm Napoleonic Austrian Army (Part 7: There's Never Enough Infantry), accessed May 4, 2026, [https://www.jemimafawr.co.uk/2025/08/16/imperial-royal-my-15mm-napoleonic-austrian-army-part-7-more-infantry/](https://www.jemimafawr.co.uk/2025/08/16/imperial-royal-my-15mm-napoleonic-austrian-army-part-7-more-infantry/)  
35. The Game \- Napoleonics \- Commands and Colors System, accessed May 4, 2026, [https://www.commandsandcolors.net/napoleonics/the-game.html](https://www.commandsandcolors.net/napoleonics/the-game.html)  
36. Collaboration: The Case of the Duchy of Warsaw (Chapter 9\) \- The Cambridge History of the Napoleonic Wars, accessed May 4, 2026, [https://www.cambridge.org/core/books/cambridge-history-of-the-napoleonic-wars/collaboration-the-case-of-the-duchy-of-warsaw/F295AD210B2CFDC935B1168844861CA5](https://www.cambridge.org/core/books/cambridge-history-of-the-napoleonic-wars/collaboration-the-case-of-the-duchy-of-warsaw/F295AD210B2CFDC935B1168844861CA5)  
37. Janissary \- Wikipedia, accessed May 4, 2026, [https://en.wikipedia.org/wiki/Janissary](https://en.wikipedia.org/wiki/Janissary)  
38. Devlet-i Âliye-i Osmâniyye | Napoleonic Wars Wiki | Fandom, accessed May 4, 2026, [https://napoleonic-wars-rblx.fandom.com/wiki/Ottoman\_Empire](https://napoleonic-wars-rblx.fandom.com/wiki/Ottoman_Empire)  
39. Why Artifact Failed \- Game Developer, accessed May 4, 2026, [https://www.gamedeveloper.com/design/why-artifact-failed](https://www.gamedeveloper.com/design/why-artifact-failed)  
40. Artifact: What Went Wrong? \- Hacker News, accessed May 4, 2026, [https://news.ycombinator.com/item?id=21199134](https://news.ycombinator.com/item?id=21199134)  
41. Richard Garfield on Artifact's failed monetization model: 'We wanted to avoid manipulating people' — The Artifact designer looks back on what went wrong. : r/Games \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/Games/comments/li9kkc/richard\_garfield\_on\_artifacts\_failed\_monetization/](https://www.reddit.com/r/Games/comments/li9kkc/richard_garfield_on_artifacts_failed_monetization/)  
42. MTG \- How To Play Two-Headed Giant \- An Introduction for Magic: The Gathering \- YouTube, accessed May 4, 2026, [https://www.youtube.com/watch?v=mjMEI752GE0](https://www.youtube.com/watch?v=mjMEI752GE0)  
43. What the hell happened in 2025? \- How To Market A Game, accessed May 4, 2026, [https://howtomarketagame.com/2026/01/27/what-the-hell-happened-in-2025/](https://howtomarketagame.com/2026/01/27/what-the-hell-happened-in-2025/)  
44. The 2024 Indie Game Landscape: Why Luck Plays a Major Role in Success on Steam, accessed May 4, 2026, [https://shahriyarshahrabi.medium.com/the-2024-indie-game-landscape-why-luck-plays-a-major-role-in-success-on-steam-c6cbc1868c35](https://shahriyarshahrabi.medium.com/the-2024-indie-game-landscape-why-luck-plays-a-major-role-in-success-on-steam-c6cbc1868c35)  
45. Most played Trading Card Game Games Steam Charts \- SteamDB, accessed May 4, 2026, [https://steamdb.info/charts/?tagid=9271](https://steamdb.info/charts/?tagid=9271)  
46. What happened to competitive card games like hearthstone? : r/truegaming \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/truegaming/comments/1j7822k/what\_happened\_to\_competitive\_card\_games\_like/](https://www.reddit.com/r/truegaming/comments/1j7822k/what_happened_to_competitive_card_games_like/)  
47. Napoleonic propaganda \- Wikipedia, accessed May 4, 2026, [https://en.wikipedia.org/wiki/Napoleonic\_propaganda](https://en.wikipedia.org/wiki/Napoleonic_propaganda)  
48. PAINTING AND PROPAGANDA: NAPOLEON AND HIS ARTISTS By JENNIFER LEIGH GIMBLETT \- The University of Arizona, accessed May 4, 2026, [https://repository.arizona.edu/bitstream/handle/10150/144321/azu\_etd\_mr\_2011\_0079\_sip1\_m.pdf?sequence=1](https://repository.arizona.edu/bitstream/handle/10150/144321/azu_etd_mr_2011_0079_sip1_m.pdf?sequence=1)  
49. Napoleonic Wars Posters for Sale \- Fine Art America, accessed May 4, 2026, [https://fineartamerica.com/shop/posters/napoleonic+wars](https://fineartamerica.com/shop/posters/napoleonic+wars)  
50. Path of Exile 2: Founder's Pack Price Comparison and Guide, accessed May 4, 2026, [https://www.allkeyshop.com/blog/path-of-exile-2-founders-pack-price-comparison-guide-news-y/](https://www.allkeyshop.com/blog/path-of-exile-2-founders-pack-price-comparison-guide-news-y/)  
51. People who bought the Founder's Pack right now : r/PlayTheBazaar \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/PlayTheBazaar/comments/1j43mle/people\_who\_bought\_the\_founders\_pack\_right\_now/](https://www.reddit.com/r/PlayTheBazaar/comments/1j43mle/people_who_bought_the_founders_pack_right_now/)  
52. Founders pack worth it in current state? and feedback for steam deck performance : r/SoulFrame \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/SoulFrame/comments/1pmxv11/founders\_pack\_worth\_it\_in\_current\_state\_and/](https://www.reddit.com/r/SoulFrame/comments/1pmxv11/founders_pack_worth_it_in_current_state_and/)  
53. Are any of the founders pack good value? :: Lost Ark Discusiones generales \- Steam Community, accessed May 4, 2026, [https://steamcommunity.com/app/1599340/discussions/0/3192487812581350710/?l=spanish](https://steamcommunity.com/app/1599340/discussions/0/3192487812581350710/?l=spanish)  
54. Unity vs. Godot: A Game Developer's Guide \- DEV Community, accessed May 4, 2026, [https://dev.to/manasajayasri/unity-vs-godot-a-game-developers-guide-2a6o](https://dev.to/manasajayasri/unity-vs-godot-a-game-developers-guide-2a6o)  
55. Switching from Unity to Godot My Experience So Far | David Amador, accessed May 4, 2026, [https://www.david-amador.com/2025/04/switching-unity-to-godot-my-experience-so-far/](https://www.david-amador.com/2025/04/switching-unity-to-godot-my-experience-so-far/)  
56. Unity vs. Godot, pros and cons of each? Which is better for an absolute beginner? \- Reddit, accessed May 4, 2026, [https://www.reddit.com/r/gamedev/comments/1fxd33a/unity\_vs\_godot\_pros\_and\_cons\_of\_each\_which\_is/](https://www.reddit.com/r/gamedev/comments/1fxd33a/unity_vs_godot_pros_and_cons_of_each_which_is/)