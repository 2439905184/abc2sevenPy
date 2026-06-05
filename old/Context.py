"""扫描器 解析器 格式化器共享的上下文，包括了错误报告，令牌/解析树节点的id生成器
   Context that’s shared between the scanner, parser, and formatter.
   Includes ErrorReporting, token/parseTreeNodes’ idGenerator
"""
class ABCContext:
    errorReporter: AbcErrorReporter
    # /** File-level linear flag from %%abcls-parse linear in file header */
    linear: bool = false
    # /** Current tune's effective linear value. Inherits from file header, can be overridden in tune header. */
    tuneLinear: bool = false
    # /** File-level formatter config from %%abcls-fmt in file header */
    formatterConfig: FormatterConfig = { ...DEFAULT_FORMATTER_CONFIG }
    # /** Current tune's effective formatter config. Inherits from file header, can be overridden in tune header. */
    tuneFormatterConfig: FormatterConfig = { ...DEFAULT_FORMATTER_CONFIG };
    def __init__(self):
        self.errorReporter = AbcErrorReporter()
        self.options = AbcContextOpys = {
            preserveComments = true,
            formatOptions: {
        alignBarlines: true,
      },
    }
    def reset(self):
        self.linear = false;
        self.tuneLinear = false;

        self.assign(self.formatterConfig, DEFAULT_FORMATTER_CONFIG);
        self.assign(self.tuneFormatterConfig, DEFAULT_FORMATTER_CONFIG);

        self.errorReporter.resetWarnings();
        self.errorReporter.resetErrors();