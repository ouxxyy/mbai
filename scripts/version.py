"""冻结契约版本的单一来源。

升级版本时只改本文件；references/report-contract.schema.json 的 const、
SKILL.md metadata 与 tests/test_version_contract.py 断言三者一致。
"""

SCHEMA_VERSION = "4.0.0"
RULE_VERSION = "4.0.0"

# 支持读取的历史版本（含当前）；早于当前版本的报告可迁移，当前版本拒绝再迁移（防双翻）。
SUPPORTED_SCHEMA_VERSIONS = ("1.0.0", "2.0.0", "3.0.0", SCHEMA_VERSION)
MIGRATABLE_SCHEMA_VERSIONS = SUPPORTED_SCHEMA_VERSIONS[:-1]
