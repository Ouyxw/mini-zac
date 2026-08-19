# Mini-ZAC M0 Core Data Model 详细开发计划

## 1. M0 定位

M0 的目标不是让 Mini-ZAC 完成真实编译，而是先稳定后续 M1–M5 都依赖的核心语义层。

M0 需要回答四个基础问题：

$$
\boxed{\text{硬件上有什么？}}
$$

$$
\boxed{\text{线路里有什么？}}
$$

$$
\boxed{\text{某个原子现在在哪里？}}
$$

$$
\boxed{\text{编译器最终输出什么指令？}}
$$

因此 M0 只实现四类核心模型：

```text
Architecture
Circuit IR
Location / Placement State
ZAIR-like Execution IR
```

M0 不负责：

- QASM parsing；
- ASAP scheduling；
- Initial placement optimization；
- Routing optimization；
- Reuse matching；
- Simulated annealing；
- MIS-based parallel routing。

这些工作从 M1 以后逐步展开。

---

# 2. M0 总体目标

完成 M0 后，应能够手工构造如下对象：

```python
architecture = Architecture.from_spec(...)

circuit = Circuit(
    num_qubits=4,
    gates=(
        UGate(...),
        CZGate(...),
    ),
)

placement = PlacementState(
    {
        QubitId(0): StorageLocation(TrapId(0)),
        QubitId(1): StorageLocation(TrapId(1)),
    }
)

program = ZAIRProgram(
    instructions=(
        Initialize(...),
        RearrangeJob(...),
        RydbergStageOp(...),
    )
)

assert program.to_json()
```

此时：

```text
Architecture
+
Circuit semantics
+
Physical state
+
Execution IR
```

已经形成完整闭环，但仍不包含 compiler optimization。

---

# 3. 推荐目录结构

建议 M0 完成后的源码目录：

```text
src/minizac/
├── __init__.py
│
├── architecture/
│   ├── __init__.py
│   ├── ids.py
│   ├── geometry.py
│   ├── site.py
│   ├── architecture.py
│   └── loader.py
│
├── circuit/
│   ├── __init__.py
│   ├── qubit.py
│   ├── gate.py
│   ├── circuit.py
│   └── stage.py
│
├── state/
│   ├── __init__.py
│   ├── location.py
│   └── placement.py
│
└── ir/
    ├── __init__.py
    ├── instruction.py
    ├── program.py
    └── serialization.py
```

测试目录：

```text
tests/
├── unit/
│   ├── architecture/
│   ├── circuit/
│   ├── state/
│   └── ir/
│
└── test_environment.py
```

M0 阶段暂时不要创建：

```text
placement/
routing/
scheduler/
verifier/
```

避免在 domain model 未稳定前进入算法层。

---

# 4. M0 分阶段实现

建议将 M0 拆成：

```text
M0.1
Typed IDs + Geometry

M0.2
Architecture Model

M0.3
Circuit IR

M0.4
Location + PlacementState

M0.5
ZAIR-like Execution IR
```

---

# 5. M0.1 — Typed IDs 与 Geometry

## 5.1 目标

建立所有核心对象使用的强类型 ID，并明确区分：

```text
Logical ID
Physical Site ID
Grid Index
Physical Coordinate
```

## 5.2 Typed IDs

不要在全项目范围内直接使用裸 `int` 表示不同对象。

```python
from typing import NewType

QubitId = NewType("QubitId", int)
TrapId = NewType("TrapId", int)
RydbergSiteId = NewType("RydbergSiteId", int)
AODId = NewType("AODId", int)
```

## 5.3 Geometry

```python
from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Position2D:
    x: float
    y: float

    def distance_to(self, other: "Position2D") -> float:
        return math.hypot(
            self.x - other.x,
            self.y - other.y,
        )
```

必须明确区分 Grid Index 与 Physical Coordinate。

---

# 6. M0.2 — Architecture Model

## 6.1 目标

描述 zoned neutral-atom hardware 的静态结构。

第一版只考虑：

```text
Single Storage Zone
+
Single Entanglement Zone
+
Single AOD
```

## 6.2 StorageTrap

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorageTrap:
    id: TrapId
    row: int
    col: int
    position: Position2D
```

## 6.3 RydbergSite

一个 Rydberg interaction site 建议建模为两个 interaction slots：

```text
Rydberg Site ω

●────●
L    R
```

```python
from enum import Enum


class RydbergSlot(Enum):
    LEFT = "left"
    RIGHT = "right"
```

```python
@dataclass(frozen=True, slots=True)
class RydbergSite:
    id: RydbergSiteId
    row: int
    col: int
    left_position: Position2D
    right_position: Position2D

    @property
    def center(self) -> Position2D:
        return Position2D(
            x=(self.left_position.x + self.right_position.x) / 2,
            y=(self.left_position.y + self.right_position.y) / 2,
        )
```

## 6.4 AOD

```python
@dataclass(frozen=True, slots=True)
class AOD:
    id: AODId
```

M0 不建模 AOD row/column、trajectory、beam frequency 等 machine-level 细节。

## 6.5 Architecture

```python
@dataclass(frozen=True, slots=True)
class Architecture:
    storage_traps: tuple[StorageTrap, ...]
    rydberg_sites: tuple[RydbergSite, ...]
    aods: tuple[AOD, ...]
```

建议提供：

```python
def get_storage_trap(self, trap_id: TrapId) -> StorageTrap:
    ...

def get_rydberg_site(self, site_id: RydbergSiteId) -> RydbergSite:
    ...
```

## 6.6 ArchitectureSpec

配置与运行时对象分离：

```python
@dataclass(frozen=True)
class ArchitectureSpec:
    storage_rows: int
    storage_cols: int
    rydberg_rows: int
    rydberg_cols: int
    storage_spacing: float
    rydberg_site_spacing: float
    pair_spacing: float
    zone_separation: float
    num_aods: int
```

然后：

```python
architecture = build_architecture(spec)
```

## 6.7 Hardware JSON

`hardware/toy_zoned.json`：

```json
{
    "storage": {
        "rows": 4,
        "cols": 8,
        "spacing": 3.0
    },
    "entanglement": {
        "rows": 2,
        "cols": 3,
        "site_spacing": 10.0,
        "pair_spacing": 2.0
    },
    "zone_separation": 20.0,
    "aod": {
        "count": 1
    }
}
```

M0 暂不引入 Pydantic / JSON Schema。

---

# 7. M0.3 — Circuit IR

## 7.1 目标

Circuit IR 描述程序想执行什么；Architecture 描述硬件拥有什么资源。二者保持解耦。

## 7.2 Gate 类型

```python
@dataclass(frozen=True, slots=True)
class UGate:
    qubit: QubitId
    theta: float
    phi: float
    lam: float
```

```python
@dataclass(frozen=True, slots=True)
class CZGate:
    q0: QubitId
    q1: QubitId

    def __post_init__(self) -> None:
        if self.q0 == self.q1:
            raise ValueError(
                "CZ gate requires two distinct qubits."
            )
```

```python
Gate = UGate | CZGate
```

## 7.3 Circuit

```python
@dataclass(frozen=True, slots=True)
class Circuit:
    num_qubits: int
    gates: tuple[Gate, ...]

    def __post_init__(self) -> None:
        if self.num_qubits <= 0:
            raise ValueError(
                "Circuit must contain at least one qubit."
            )

        for gate in self.gates:
            self._validate_gate(gate)
```

需要检查：

$$
0 \le q < n
$$

## 7.4 RydbergStage

M0 只定义语义，不实现 stage generation：

```python
@dataclass(frozen=True, slots=True)
class RydbergStage:
    index: int
    gates: tuple[CZGate, ...]
```

同一 qubit 在同一 stage 中最多参与一个 two-qubit gate。

---

# 8. M0.4 — Location 与 PlacementState

## 8.1 目标

连接 Logical Circuit 与 Physical Architecture，明确表达：

```text
Qubit → Physical Location
```

## 8.2 StorageLocation

```python
@dataclass(frozen=True, slots=True)
class StorageLocation:
    trap_id: TrapId
```

## 8.3 RydbergLocation

```python
@dataclass(frozen=True, slots=True)
class RydbergLocation:
    site_id: RydbergSiteId
    slot: RydbergSlot
```

```python
StaticLocation = StorageLocation | RydbergLocation
```

M0 暂不加入 AODLocation。

## 8.4 PlacementState

```python
from types import MappingProxyType


@dataclass(frozen=True)
class PlacementState:
    locations: Mapping[QubitId, StaticLocation]

    def __post_init__(self) -> None:
        copied = MappingProxyType(dict(self.locations))
        object.__setattr__(self, "locations", copied)
```

推荐 immutable snapshot：

```text
PlacementState
    ↓ transition
PlacementState'
```

## 8.5 Single Source of Truth

只保存：

```text
Qubit → Location
```

反向 occupancy 动态计算：

```python
def occupant_of(
    self,
    location: StaticLocation,
) -> QubitId | None:
    ...
```

## 8.6 Placement Invariants

必须检查：

```text
Storage collision
Rydberg slot collision
```

但允许：

```text
q0 → site 2 / left
q1 → site 2 / right
```

---

# 9. M0.5 — ZAIR-like Execution IR

## 9.1 目标

Circuit IR 表达：

```text
What should be computed?
```

ZAIR-like IR 表达：

```text
What should the neutral-atom hardware do?
```

## 9.2 AtomPlacement / Initialize

```python
@dataclass(frozen=True, slots=True)
class AtomPlacement:
    qubit: QubitId
    location: StaticLocation
```

```python
@dataclass(frozen=True, slots=True)
class Initialize:
    placements: tuple[AtomPlacement, ...]
```

## 9.3 OneQOp

```python
@dataclass(frozen=True, slots=True)
class OneQOp:
    qubit: QubitId
    theta: float
    phi: float
    lam: float
```

## 9.4 AtomMove

```python
@dataclass(frozen=True, slots=True)
class AtomMove:
    qubit: QubitId
    source: StaticLocation
    target: StaticLocation
```

## 9.5 RearrangeJob

```python
@dataclass(frozen=True, slots=True)
class RearrangeJob:
    aod_id: AODId
    moves: tuple[AtomMove, ...]
```

避免使用 `qubits[] / sources[] / targets[]` 三组平行数组。

## 9.6 RydbergCZ

```python
@dataclass(frozen=True, slots=True)
class RydbergCZ:
    site_id: RydbergSiteId
    q0: QubitId
    q1: QubitId
```

## 9.7 RydbergStageOp

```python
@dataclass(frozen=True, slots=True)
class RydbergStageOp:
    gates: tuple[RydbergCZ, ...]
```

## 9.8 Instruction Union

```python
Instruction = (
    Initialize
    | OneQOp
    | RearrangeJob
    | RydbergStageOp
)
```

## 9.9 ZAIRProgram

```python
@dataclass(frozen=True, slots=True)
class ZAIRProgram:
    instructions: tuple[Instruction, ...]
```

---

# 10. ZAIR Serialization

M0 就稳定 serialization boundary。

示例：

```json
{
    "version": "0.1",
    "instructions": [
        {
            "op": "init",
            "placements": [
                {
                    "qubit": 0,
                    "location": {
                        "kind": "storage",
                        "trap": 0
                    }
                }
            ]
        },
        {
            "op": "rearrange",
            "aod": 0,
            "moves": [
                {
                    "qubit": 0,
                    "source": {
                        "kind": "storage",
                        "trap": 0
                    },
                    "target": {
                        "kind": "rydberg",
                        "site": 2,
                        "slot": "left"
                    }
                }
            ]
        }
    ]
}
```

所有 union 类型建议使用 discriminator：

```text
kind
op
```

建议实现：

```text
to_dict
from_dict
to_json
from_json
```

不要直接暴露 `dataclasses.asdict()` 作为公共 IR 格式。

---

# 11. JSON Round Trip

M0 必须支持：

```python
program == ZAIRProgram.from_json(
    program.to_json()
)
```

即：

```text
Python Object
    ↓
JSON
    ↓
Python Object
```

语义保持不变。

---

# 12. State Transition Helper

M0 可以实现：

```python
def apply_rearrange_job(
    state: PlacementState,
    job: RearrangeJob,
) -> PlacementState:
    ...
```

只负责：

```text
Current State
+
RearrangeJob
↓
New State
```

不负责复杂 AOD legality。

---

# 13. M0 Scope Boundary

M0 不实现：

```text
QASM frontend
ASAP scheduler
Initial placement
Dynamic placement
Movement optimization
Reuse matching
Simulated annealing
Parallel AOD grouping
MIS
Fidelity estimation
Full verifier
```

M0 中不应出现核心 `optimize(...)` 逻辑。

---

# 14. 推荐 Commit 顺序

建议 8 个 commit：

## Commit 1

```text
feat: add typed hardware and qubit identifiers
```

实现：

```text
QubitId
TrapId
RydbergSiteId
AODId
Position2D
```

## Commit 2

```text
feat: add zoned architecture model
```

实现：

```text
StorageTrap
RydbergSite
RydbergSlot
AOD
Architecture
```

## Commit 3

```text
feat: add architecture spec loader
```

实现：

```text
ArchitectureSpec
toy_zoned.json
JSON loader
build_architecture()
```

## Commit 4

```text
feat: add logical circuit IR
```

实现：

```text
UGate
CZGate
Circuit
RydbergStage
```

## Commit 5

```text
feat: add physical location model
```

实现：

```text
StorageLocation
RydbergLocation
StaticLocation
PlacementState
```

## Commit 6

```text
feat: add ZAIR instruction model
```

实现：

```text
AtomPlacement
Initialize
OneQOp
AtomMove
RearrangeJob
RydbergCZ
RydbergStageOp
ZAIRProgram
```

## Commit 7

```text
feat: add ZAIR JSON serialization
```

实现：

```text
to_dict
from_dict
to_json
from_json
```

以及 round-trip tests。

## Commit 8

```text
test: complete M0 domain model coverage
```

补全 unit tests 与 integration test。

---

# 15. M0 测试矩阵

| Test | 目标 |
|---|---|
| Architecture generation | trap/site 数量正确 |
| Coordinate uniqueness | physical slot 唯一 |
| Invalid architecture | 非法 rows/spacing 被拒绝 |
| Circuit bounds | logical qubit 不越界 |
| CZ self interaction | `CZ(q0,q0)` 被拒绝 |
| Stage conflict | 同一 qubit 不可同 stage 参与两门 |
| Storage collision | 两 atom 不可占同 storage trap |
| Rydberg slot collision | 两 atom 不可占同 slot |
| Legal Rydberg pair | 同 site 左右 slot 可分别占据 |
| Rearrange transition | movement 后 state 正确 |
| ZAIR serialization | JSON 内容正确 |
| ZAIR roundtrip | encode/decode 不丢语义 |

---

# 16. M0 Integration Test

建议手工构造最小 Bell execution。

初态：

```text
q0 → S0
q1 → S1
```

移动：

```text
q0 → ω0.left
q1 → ω0.right
```

执行：

```text
CZ(q0,q1)
```

示例：

```python
program = ZAIRProgram(
    instructions=(
        Initialize(
            placements=(
                AtomPlacement(
                    QubitId(0),
                    StorageLocation(TrapId(0)),
                ),
                AtomPlacement(
                    QubitId(1),
                    StorageLocation(TrapId(1)),
                ),
            ),
        ),

        RearrangeJob(
            aod_id=AODId(0),
            moves=(
                AtomMove(
                    QubitId(0),
                    StorageLocation(TrapId(0)),
                    RydbergLocation(
                        RydbergSiteId(0),
                        RydbergSlot.LEFT,
                    ),
                ),
                AtomMove(
                    QubitId(1),
                    StorageLocation(TrapId(1)),
                    RydbergLocation(
                        RydbergSiteId(0),
                        RydbergSlot.RIGHT,
                    ),
                ),
            ),
        ),

        RydbergStageOp(
            gates=(
                RydbergCZ(
                    site_id=RydbergSiteId(0),
                    q0=QubitId(0),
                    q1=QubitId(1),
                ),
            ),
        ),
    ),
)
```

该测试用于验证：

$$
Architecture
+
Location
+
Circuit\ Semantics
+
ZAIR
$$

可以协同工作。

---

# 17. M0 Acceptance Criteria

## Architecture

```text
[ ] toy architecture 可从 JSON 加载
[ ] Storage trap 唯一
[ ] Rydberg slot 唯一
[ ] Architecture immutable
[ ] Architecture 查询 API 可用
```

## Circuit

```text
[ ] U/CZ 可表达
[ ] Logical qubit bounds 可验证
[ ] CZ self interaction 被拒绝
[ ] RydbergStage 有合法性约束
```

## State

```text
[ ] StorageLocation 可表达
[ ] RydbergLocation 可表达
[ ] PlacementState immutable
[ ] Storage collision 可检测
[ ] Rydberg slot collision 可检测
```

## ZAIR

```text
[ ] Initialize
[ ] OneQOp
[ ] RearrangeJob
[ ] RydbergStageOp
[ ] ZAIRProgram
[ ] JSON serialization
[ ] JSON deserialization
[ ] JSON round-trip
```

## Quality

```text
[ ] pytest passes
[ ] Ruff passes
[ ] mypy passes
```

---

# 18. M0 最终架构边界

```text
┌────────────────────────────┐
│       Circuit IR           │
│                            │
│ Qubit / U / CZ / Stage     │
│                            │
│ "What should be computed?" │
└─────────────┬──────────────┘
              │
              │ compiler
              ▼
┌────────────────────────────┐
│      Physical State        │
│                            │
│ Qubit → Location           │
│                            │
│ "Where are atoms?"         │
└─────────────┬──────────────┘
              │
              │ constrained by
              ▼
┌────────────────────────────┐
│       Architecture         │
│                            │
│ Storage / Rydberg / AOD    │
│                            │
│ "What hardware exists?"    │
└────────────────────────────┘


              ↓ produces


┌────────────────────────────┐
│        ZAIR                │
│                            │
│ Init / Move / U / Rydberg  │
│                            │
│ "What should hardware do?" │
└────────────────────────────┘
```

---

# 19. 三个必须坚持的工程原则

## 19.1 不混用裸 int

使用：

```text
QubitId
TrapId
RydbergSiteId
AODId
```

## 19.2 PlacementState 使用 immutable snapshot

推荐：

```text
State
↓
Transition
↓
New State
```

而不是共享 mutable dict。

## 19.3 RearrangeJob 使用 AtomMove

推荐：

```python
RearrangeJob(
    moves=(
        AtomMove(...),
        AtomMove(...),
    )
)
```

不要使用三组平行数组。

---

# 20. M0 完成后的下一步

M0 完成后，M1 的第一项工作：

$$
\boxed{
\text{Qiskit Circuit}
\rightarrow
\text{Mini-ZAC Circuit IR}
}
$$

然后实现：

$$
\boxed{
\text{Circuit IR}
\rightarrow
\text{RydbergStage[]}
}
$$

即：

```text
Qiskit Frontend
        ↓
Mini-ZAC Circuit IR
        ↓
ASAP Rydberg Stage Scheduling
```

---

# 21. M0 完成定义

当以下链路成立：

```text
Hardware Spec
      ↓
Architecture
      +
Circuit IR
      +
PlacementState
      +
ZAIRProgram
      ↓
Serialization
      ↓
Unit Tests
```

并且：

```text
pytest
ruff
mypy
```

全部通过，即可认为：

```text
M0 — Core Data Model
```

正式完成。
