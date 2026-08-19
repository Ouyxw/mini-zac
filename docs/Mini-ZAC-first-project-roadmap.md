## 1. 项目定位

Mini-ZAC First Project 的目标不是完整复刻 UCLA ZAC，而是构建一个 **ZAC-compatible、可验证、可扩展的 zoned neutral-atom compiler skeleton**，并逐步复现 ZAC 最核心的编译思想：

```text
OpenQASM / QuantumCircuit
        ↓
Circuit Lowering
        ↓
Rydberg Stage Scheduling
        ↓
Initial Placement
        ↓
Dynamic / Reuse-Aware Placement
        ↓
Movement Routing
        ↓
Execution Scheduling
        ↓
ZAIR-like IR
        ↓
Verifier + Metrics
```

第一阶段聚焦单一硬件模型：

```text
Single Storage Zone
+
Single Entanglement Zone
+
Single AOD
```

暂不处理：

- Multi-AOD；
- Multi-entanglement-zone；
- Mid-circuit measurement；
- 完整 machine-level AOD 指令综合；
- QEC / QLDPC；
- QLLVM integration；
- 全局 ILP / SMT 最优求解。

---

# 2. First Project 的核心研究问题

第一版希望回答三个问题：
$$
\boxed{\text{Initial Placement 是否显著影响移动开销？}}
$$
$$
\boxed{\text{Reuse-Aware Placement 是否能够减少 atom transfer？}}
$$
$$
\boxed{\text{Parallel Routing 是否能够减少 rearrangement depth？}}
$$

因此整个项目采用逐轮递进方式开发：
```text
M0
Core Data Model
        ↓
M1
Correct Compiler
        ↓
M2
Dynamic Placement
        ↓
M3
Reuse-Aware Placement
        ↓
M4
Initial Placement Optimization
        ↓
M5
Parallel Routing
```

---

# 3. 总体模块结构

建议最终模块划分：

```text
src/minizac/
│
├── frontend/
│   ├── qasm.py
│   └── circuit.py
│
├── architecture/
│   ├── architecture.py
│   ├── zone.py
│   ├── trap.py
│   └── aod.py
│
├── ir/
│   ├── instruction.py
│   └── zair.py
│
├── scheduler/
│   └── gate_scheduler.py
│
├── placement/
│   ├── trivial.py
│   ├── simulated_annealing.py
│   ├── reuse.py
│   └── dynamic.py
│
├── routing/
│   ├── sequential.py
│   └── parallel.py
│
├── scheduling/
│   └── asap.py
│
├── verifier/
│   └── verifier.py
│
├── metrics/
│   ├── latency.py
│   ├── movement.py
│   └── fidelity.py
│
└── compiler.py
```

---

# 4. Round M0 — Core Data Model

## 4.1 目标

建立后续所有算法依赖的核心 domain model。

这一轮不做：

- Placement optimization；
- Routing optimization；
- Scheduling optimization。

只定义：

```text
Architecture
Location
Circuit
ZAIR
```

---

## 4.2 Architecture

第一版使用 toy zoned architecture：

```text
Storage Zone
────────────────────────────
● ● ● ● ● ● ● ●
● ● ● ● ● ● ● ●
● ● ● ● ● ● ● ●
● ● ● ● ● ● ● ●

          ↑ AOD
          │
          ▼

Entanglement Zone
────────────────────────────
(● ●)    (● ●)    (● ●)
 ω0       ω1       ω2

(● ●)    (● ●)    (● ●)
 ω3       ω4       ω5
```

建议数据模型：

```python
Architecture(
    storage_rows=4,
    storage_cols=8,
    rydberg_rows=2,
    rydberg_cols=3,
    storage_spacing=3.0,
    rydberg_site_spacing=10.0,
    pair_spacing=2.0,
    zone_separation=10.0,
    num_aods=1,
)
```

需要定义：

```text
Architecture
Zone
SLMTrap
RydbergSite
AOD
```

---

## 4.3 Location

必须明确区分：

```text
Logical Qubit
Physical Atom
Physical Location
```

建议至少包含：

```text
StorageLocation
RydbergLocation
AODLocation
```

避免长期使用：

```python
tuple[int, int]
```

表示所有位置。

---

## 4.4 Circuit Model

第一版 circuit 只需要支持：

```text
U / U3
CZ
```

建议类型：

```text
LogicalQubit
OneQGate
CZGate
Circuit
Stage
```

---

## 4.5 ZAIR-like IR

第一版不设计 MLIR dialect。

使用 Python dataclass：

```python
@dataclass
class Init:
    qubit: int
    location: QubitLocation


@dataclass
class OneQGate:
    qubit: int
    gate: str
    params: list[float]


@dataclass
class Rydberg:
    zone_id: int
    gates: list[tuple[int, int]]


@dataclass
class RearrangeJob:
    aod_id: int
    qubits: list[int]
    begin_locations: list[QubitLocation]
    end_locations: list[QubitLocation]
```

最终支持 JSON serialization。

---

## 4.6 M0 验收标准

```text
[ ] Architecture 可以实例化
[ ] Storage / Rydberg site 坐标唯一
[ ] LogicalQubit 与 Physical Location 类型分离
[ ] Circuit 可以表达 U/CZ
[ ] ZAIR instruction 可序列化
[ ] 基础 domain model 有 unit tests
```

---

# 5. Round M1 — Correct Compiler

## 5.1 目标

实现第一条完整但不优化的编译链：

```text
QASM / QuantumCircuit
        ↓
U/CZ lowering
        ↓
Rydberg stages
        ↓
Trivial placement
        ↓
Sequential movement
        ↓
ZAIR
        ↓
Verifier
```

这一轮唯一目标：

> 编译正确。

不追求：

- movement distance；
- transfer count；
- execution latency。

---

# 6. M1.1 — Frontend

输入：

```text
OpenQASM
```

或：

```python
compile(QuantumCircuit)
```

使用 Qiskit 将线路 lower 到：

```text
{U, CZ}
```

然后转换为 Mini-ZAC 自己的 Circuit IR。

输出：

```text
Circuit
├── LogicalQubits
└── Gates
```

---

# 7. M1.2 — Rydberg Stage Scheduling

建立 circuit DAG。

将 CZ gates 分层为：

```text
Rydberg Stage 0
Rydberg Stage 1
...
```

采用 ASAP scheduling。

基本约束：

$$
\forall q,\qquad
\#\{g\in L_k\mid q\in g\}\leq 1
$$

即一个 qubit 在同一 stage 中最多参与一个 two-qubit gate。

示例：

```text
CZ(q0,q1)
CZ(q2,q3)
CZ(q0,q2)
CZ(q1,q3)
```

得到：

```text
Stage 0
CZ(q0,q1)
CZ(q2,q3)

Stage 1
CZ(q0,q2)
CZ(q1,q3)
```

---

# 8. M1.3 — Trivial Initial Placement

第一版只实现：

```text
q0 → storage[0,0]
q1 → storage[0,1]
q2 → storage[0,2]
...
```

不做 optimization。

目的：

- 验证 architecture；
- 验证 routing；
- 验证 ZAIR；
- 验证 verifier。

---

# 9. M1.4 — Sequential Router

根据 stage 前后 placement 变化生成：

```text
RearrangeJob
```

例如：

```text
before:
q0 → storage[0,0]

after:
q0 → rydberg[0,1]
```

生成：

```python
RearrangeJob(
    qubits=[q0],
    begin=[storage[0,0]],
    end=[rydberg[0,1]],
)
```

第一版所有 movement 串行：

```text
MOVE(q0)
MOVE(q1)
MOVE(q2)
...
```

优势：

```text
Correctness > Performance
```

---

# 10. M1.5 — Basic Scheduling

Single AOD 条件下：

```text
Move-to-Entanglement
        ↓
Rydberg Gate
        ↓
Move-to-Storage
        ↓
Next Stage
```

采用 ASAP。

追踪两类依赖：

## Qubit dependency

```text
MOVE(q0)
   ↓
CZ(q0,q1)
   ↓
MOVE(q0)
```

## Trap dependency

如果：

```text
Job A:
q0 leaves storage trap S

Job B:
q5 enters storage trap S
```

则：

```text
A → B
```

---

# 11. M1.6 — Verifier

Verifier 是 M1 的核心模块之一。

至少检查：

## Atom uniqueness

$$
loc(q_i)\neq loc(q_j)
$$

合法 Rydberg pair 除外。

## Qubit conservation

每个 logical qubit 始终存在且只有一个 location。

## Gate legality

执行：

$$
CZ(q_i,q_j)
$$

时，两原子必须位于同一合法 Rydberg interaction site。

## Stage legality

一个 qubit 不能同时参与两个 two-qubit gates。

## Trap collision

任何时刻一个 SLM trap 最多被一个 atom 占据。

## Movement dependency

同一 atom 不得同时出现在两个 movement job 中。

---

# 12. M1 验收标准

```text
[ ] QASM / QuantumCircuit 可输入
[ ] 成功 lower 到 U/CZ
[ ] CZ 可正确分为 Rydberg stages
[ ] Trivial placement 可生成
[ ] Sequential RearrangeJob 可生成
[ ] ZAIR 可输出
[ ] Verifier 可检查完整执行序列
[ ] Bell / GHZ 小线路通过 integration test
```

达到这里：

```text
Mini-ZAC = Correct Compiler
```

---

# 13. Round M2 — Dynamic Placement

## 13.1 目标

开始优化每个 Rydberg stage 的 gate placement。

问题：

```text
CZ Gate
     ↓
Which Rydberg Site?
```

---

## 13.2 Gate-to-Site Assignment

构造 bipartite graph：

```text
CZ Gates
   ↕
Rydberg Sites
```

edge weight：

$$
w(g,\omega)
=
gCost(g,\omega,M)
$$

目标：

$$
\min
\sum_{g,\omega}
x_{g,\omega} w(g,\omega)
$$

约束：

$$
\sum_\omega x_{g,\omega}=1
$$

$$
\sum_g x_{g,\omega}\leq1
$$

使用：

```python
scipy.optimize.linear_sum_assignment
```

即可。

不需要自己实现 Hungarian algorithm。

---

# 14. Movement Proxy

对于 gate：

$$
g(q_i,q_j)
$$

放到 Rydberg site：

$$
\omega
$$

可采用 ZAC 风格 movement cost：

$$
gCost(g,\omega,M)
=
\begin{cases}
\sqrt{d(\omega,m_i)}
+
\sqrt{d(\omega,m_j)},
& y_i\neq y_j\\[4pt]
\max
\left(
\sqrt{d(\omega,m_i)},
\sqrt{d(\omega,m_j)}
\right),
& y_i=y_j
\end{cases}
$$

第一版也可先采用更简单：

$$
d(q_i,\omega)+d(q_j,\omega)
$$

等编译流程稳定后再恢复 ZAC proxy。

---

# 15. Non-Reused Qubit Placement

每个 stage 完成后：

```text
non-reused qubit
      ↓
return to storage
```

M2 第一版采用：

$$
\min_s d(q,s)
$$

即 nearest-empty-trap。

---

# 16. M2 验收标准

比较：

```text
Trivial gate-to-site placement
vs
Minimum-cost assignment
```

至少输出：

```text
Total movement distance
Transfer count
Execution time proxy
```

要求：

```text
[ ] Assignment 结果无 site conflict
[ ] Compiler correctness 不退化
[ ] 至少一个 benchmark 上 movement cost 改善
```

---

# 17. Round M3 — Reuse-Aware Placement

## 17.1 目标

实现 ZAC first project 中最核心的优化：

```text
Qubit Reuse
```

核心思想：

如果某个 qubit：

```text
Stage k
   ↓
Stage k+1
```

连续参与 Rydberg gate，则尽量不要：

```text
Entanglement
→ Storage
→ Entanglement
```

而是直接：

```text
keep in Entanglement Zone
```

---

# 18. Reuse Matching

考虑：

```text
Stage 0:
CZ(q0,q1)
CZ(q2,q3)

Stage 1:
CZ(q0,q2)
CZ(q1,q4)
```

构造：

$$
G_{\mathrm{reuse}}
=
(L_k,L_{k+1},E)
$$

若两个 gates 共享 qubit，则建立 edge。

然后求：

$$
\text{Maximum Cardinality Matching}
$$

目标：

$$
\max N_{\mathrm{reused}}
$$

建议亲手实现：

```text
Hopcroft–Karp
```

接口：

```python
find_reusable_qubits(
    current_stage,
    next_stage,
)
```

输出：

```python
ReuseDecision(
    qubit=0,
    current_gate=0,
    next_gate=2,
    rydberg_site=3,
)
```

---

# 19. M3 Benchmark

专门设计：

```text
Reuse Stress Test
```

例如：

```text
Stage 0
(q0,q1)
(q2,q3)
(q4,q5)

Stage 1
(q0,q2)
(q1,q4)
(q3,q5)

Stage 2
(q0,q4)
(q1,q5)
(q2,q3)
```

比较：

```text
reuse = OFF
vs
reuse = ON
```

---

# 20. Reuse Metrics

定义：

$$
ReuseRatio
=
\frac{N_{\mathrm{reused}}}
{N_{\mathrm{reuse\ candidate}}}
$$

并统计：

```text
Reuse count
Transfer count
Movement distance
Execution time
Estimated fidelity
```

---

# 21. M3 验收标准

至少满足：

$$
N_{\mathrm{transfer}}^{reuse}
<
N_{\mathrm{transfer}}^{no-reuse}
$$

并保证：

```text
[ ] Reuse matching 正确
[ ] 不产生 Rydberg site conflict
[ ] Verifier 全部通过
[ ] Reuse OFF / ON 可配置
[ ] 有可重复 benchmark 结果
```

达到 M3 后，Mini-ZAC 已经具备 first project 的核心研究价值。

---

# 22. Round M4 — Initial Placement Optimization

## 22.1 目标

从：

```text
Trivial Initial Placement
```

升级为：

```text
Simulated Annealing Initial Placement
```

研究：

```text
Initial Placement
        ↓
How much does it affect
later movement cost?
```

---

# 23. Initial Placement Cost

可以定义：

$$
C(M)
=
\sum_{g\in G_{2Q}}
gCost
\left(
g,
\omega_g^{near},
M
\right)
$$

其中：

```text
M
```

是：

```text
logical qubit
→
initial storage trap
```

映射。

---

# 24. Simulated Annealing

状态：

```text
Initial Placement Mapping
```

邻域操作：

```text
swap(q_i, q_j)
```

接受概率：

$$
P =
\exp
\left(
-\frac{\Delta C}{T}
\right)
$$

第一版必须支持 deterministic seed：

```python
seed=42
```

保证实验可复现。

---

# 25. M4 Ablation

比较：

```text
trivial placement
vs
SA placement
```

在：

```text
reuse OFF
reuse ON
```

两种条件下分别运行。

得到：

| Initial Placement | Reuse | Transfers | Distance | Time |
|---|---:|---:|---:|---:|
| Trivial | OFF | ... | ... | ... |
| Trivial | ON | ... | ... | ... |
| SA | OFF | ... | ... | ... |
| SA | ON | ... | ... | ... |

---

# 26. M4 验收标准

```text
[ ] SA 可运行
[ ] 固定 seed 可复现
[ ] trivial / SA 可切换
[ ] 至少一个 benchmark movement cost 改善
[ ] Compile time 有记录
```

---

# 27. Round M5 — Parallel Routing

## 27.1 目标

将：

```text
Sequential Movement
```

升级为：

```text
Parallel Rearrangement Jobs
```

研究：

```text
Movement compatibility
        ↓
Parallel grouping
        ↓
Reduced rearrangement depth
```

---

# 28. Movement Compatibility Graph

每一个 movement：

$$
m_i
$$

表示：

```text
atom
begin location
end location
```

构造 compatibility / conflict graph。

如果两个 movement：

```text
m_i
m_j
```

可以由同一个 AOD job 并行执行，则：

```text
compatible
```

否则：

```text
conflict
```

---

# 29. MIS-Based Grouping

使用：

```text
Maximal Independent Set
```

将兼容 movement 分成 parallel groups：

```text
Movement Set
     ↓
Conflict Graph
     ↓
MIS
     ↓
RearrangeJob
```

第一版不要求 maximum independent set。

只需要：

```text
greedy maximal independent set
```

即可。

---

# 30. Parallel Routing 输出

Sequential：

```text
Job 0: q0
Job 1: q1
Job 2: q2
Job 3: q3
```

Parallel：

```text
Job 0: q0, q2
Job 1: q1, q3
```

主要关注：

```text
Rearrange Job Count
Rearrange Depth
Movement Makespan
```

---

# 31. M5 验收标准

比较：

```text
sequential routing
vs
parallel routing
```

要求：

```text
[ ] Parallel job 满足 AOD compatibility
[ ] Verifier 通过
[ ] Rearrangement depth 不增加
[ ] 至少一个 benchmark depth 降低
[ ] sequential / parallel 可配置
```

达到这里：

```text
Mini-ZAC First Project
```

可以视为完成。

---

# 32. Metrics

从 M2 开始逐步加入 metrics。

最终至少记录：

```text
Circuit
Qubits
1Q Gates
2Q Gates
Rydberg Stages

Reuse Count
Reuse Ratio

Atom Transfers
Atom Movements
Total Movement Distance
Rearrange Job Count
Rearrange Depth

Movement Makespan
Estimated Execution Time

Estimated Fidelity
Compile Time
```

---

# 33. Movement Time Proxy

可采用：

$$
\frac{d}{t^2}
=
2750\,\mathrm{m/s^2}
$$

即：

$$
t
=
\sqrt{\frac{d}{2750}}
$$

因此 placement / routing cost 中使用：

$$
\sqrt{d}
$$

是合理 proxy。

---

# 34. Fidelity Proxy

可采用：

$$
F=
f_1^{g_1}
f_2^{g_2}
f_{\mathrm{exc}}^{N_{\mathrm{exc}}}
f_{\mathrm{tran}}^{N_{\mathrm{tran}}}
\prod_{q\in Q}
\left(
1-\frac{t_q}{T_2}
\right)
$$

所有参数必须放在：

```text
hardware config
```

不要 hard-code。

---

# 35. Benchmark Set

第一版建议：

| Benchmark | 主要用途 |
|---|---|
| Bell pairs | 最简单 CZ placement |
| GHZ | 高 reuse |
| Linear nearest-neighbor | Locality |
| QFT | Dense interaction |
| Random CZ layers | Generic routing |
| Reuse Stress Test | Reuse effectiveness |

项目稳定后再扩展到：

```text
QASMBench
```

---

# 36. 最终 Ablation Matrix

建议最终至少支持：

```text
Initial Placement
├── trivial
└── simulated annealing

Reuse
├── OFF
└── ON

Routing
├── sequential
└── parallel
```

即：

$$
2\times2\times2=8
$$

种基础配置。

例如：

| Placement | Reuse | Routing |
|---|---|---|
| Trivial | OFF | Sequential |
| Trivial | OFF | Parallel |
| Trivial | ON | Sequential |
| Trivial | ON | Parallel |
| SA | OFF | Sequential |
| SA | OFF | Parallel |
| SA | ON | Sequential |
| SA | ON | Parallel |

---

# 37. First Project 最终验收

## AC1 — Compilation Correctness

所有 benchmark：

```text
QASM
 ↓
Mini-ZAC
 ↓
ZAIR
```

通过 verifier。

---

## AC2 — Physical Legality

所有 CZ gate 执行时：

```text
two atoms
↓
valid Rydberg interaction site
```

且：

```text
No trap collision
No duplicate atom
No illegal movement overlap
```

---

## AC3 — Reuse Effectiveness

至少一个 benchmark：

$$
N_{\mathrm{transfer}}^{reuse}
<
N_{\mathrm{transfer}}^{no-reuse}
$$

---

## AC4 — Reproducibility

固定：

```text
random seed
hardware config
compiler config
```

结果可重复。

---

## AC5 — Ablation

必须支持：

```text
trivial / SA
reuse OFF / ON
sequential / parallel
```

---

# 38. First Project 完成后的技术能力边界

完成 M0–M5 后，应已经掌握：

```text
Circuit Frontend
        ↓
Rydberg Stage Scheduling
        ↓
Initial Placement
        ↓
Dynamic Placement
        ↓
Reuse Matching
        ↓
Movement Routing
        ↓
Execution Scheduling
        ↓
ZAIR
        ↓
Verification
```

尤其是三个核心算法：

$$
\boxed{
\text{Hopcroft–Karp Reuse Matching}
}
$$

$$
\boxed{
\text{Minimum-Cost Gate/Site Assignment}
}
$$

$$
\boxed{
\text{MIS-Based Parallel Movement Grouping}
}
$$

---

# 39. First Project 之后的路线

完成之后可以自然进入：

```text
Project 1
Mini-ZAC
Single Zone / Single AOD
        │
        ▼
Project 2
Routing-Aware Placement
Placement ↔ Routing Co-optimization
        │
        ▼
Project 3
Multi-AOD / Multi-Zone Scheduling
        │
        ▼
Project 4
Hardware-Aware IR / QLLVM Lowering
        │
        ▼
Project 5
Logical Block / QLDPC Compilation
```

因此 First Project 的真正定位不是：

```text
Reproduce ZAC
```

而是：

> 构建一个 ZAC-compatible research compiler skeleton，并逐步复现 reuse-aware placement、initial placement optimization 和 parallel routing 的核心思想。

