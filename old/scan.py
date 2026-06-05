from enum import Enum ,auto
# token types
class TokenType(Enum):
    ACCIDENTAL = auto()
    AMPERSAND = auto() # &
    ANNOTATION = auto()
    BARLINE = auto() #|
    BCKTCK_SPC = auto()
    CHRD_LEFT_BRKT = auto()
    CHRD_RIGHT_BRKT = auto()
    DISCARD = auto() # used only by generators
    EQL = auto()
    SLASH = auto() # Slash separator (/)
    MINUS = auto() # minus operator (-)
    PLUS = auto() # Addition operator (+)
    LPAREN = auto() # Left parenthesis (
    RPAREN = auto() # Right parenthesis )
    LBRACE = auto() # Left brace {
    RBRACE = auto() # Right brace }
    LBRACKET = auto() # Left bracket [
    RBRACKET = auto() # Right bracket ]
    PIPE = auto() # Pipe symbol | (for directive context different from BARLINE)
    IDENTIFIER = auto() # Unquoted words (treble major etc.)
    NUMBER = auto() # Integer or float numbers (1 4 120 1.5)
    SPECIAL_LITERAL = auto() # Special cases (C C|)
    COMMENT = auto()
    DECORATION = auto()
    SYSTEM_BREAK = auto()# System break ( ! )
    EOF = auto()
    EOL = auto()
    ESCAPED_CHAR = auto()
    FREE_TXT = auto()
    GRC_GRP_LEFT_BRACE = auto()
    GRC_GRP_RGHT_BRACE = auto()
    GRC_GRP_SLSH = auto()
    INF_CTND = auto()# field continuation
    INFO_STR = auto()
    INF_HDR = auto()
    LINE_CONT = auto()# line continuation (\)
    INLN_FLD_LFT_BRKT = auto()
    INLN_FLD_RGT_BRKT = auto()
    INVALID = auto()# For invalid tokens that should be preserved
    LY_HDR = auto()# lyric header
    LY_HYPH = auto()
    LY_SECT_HDR = auto()
    LY_SPS = auto()
    LY_STAR = auto()
    LY_TXT = auto()
    LY_UNDR = auto()
    MACRO_HDR = auto()
    MACRO_INVOCATION = auto()
    MACRO_STR = auto()
    MACRO_VAR = auto()
    MEASUREMENT_UNIT = auto() # For measurement units (in cm pt etc.)
    NOTE_LETTER = auto()
    OCTAVE = auto()
    RESERVED_CHAR = auto()
    REST = auto()
    RHY_BRKN = auto()
    RHY_DENOM = auto()
    RHY_NUMER = auto()
    RHY_SEP = auto()
    SCT_BRK = auto()
    SLUR = auto()
    DOTTED_SLUR = auto() # .( for dotted slur
    STYLESHEET_DIRECTIVE = auto() # %%
    SYMBOL = auto()# ![a-zA-Z]!
    TIE = auto()
    TUPLET_LPAREN = auto() # Opening parenthesis of a tuplet (
    TUPLET_P = auto() # The p value in a tuplet
    TUPLET_COLON = auto()# The colon separator in a tuplet :
    TUPLET_Q = auto() # The q value in a tuplet
    TUPLET_R = auto() # The r value in a tuplet
    USER_SY_HDR = auto()
    USER_SY = auto() # user-symbol
    USER_SY_INVOCATION = auto()
    VOICE = auto()
    VOICE_OVRLAY = auto()
    WS = auto()
    Y_SPC = auto()
    REPEAT_NUMBER = auto() # For repeat numbers (1 2 3 etc.)
    REPEAT_COMMA = auto() # For commas separating numbers (123)
    REPEAT_DASH = auto() # For dashes in ranges (1-3)
    REPEAT_X = auto() # For 'x' notation (1x2)
    SY_HDR = auto() # symbol line header
    SY_STAR = auto() # symbol line star
    SY_TXT = auto() # symbol line text
    CHORD_SYMBOL = auto() # ABCx chord symbol (e.g. Am7 Cmaj7#11 Bb/D)
    KEY_SIGNATURE = auto() # Key signature (e.g. C#m Dmaj F# Gdor HP none)
def Scanner(source:str abcContext: ABCContext):
    ctx = new Ctx(source abcContext)
    while (!isAtEnd(ctx)):
        ctx.start = ctx.current;
        fileStructure(ctx)
    ctx.push(TokenType.EOF)
    return ctx.tokens

def fileStructure(ctx: Ctx):
    while (!isAtEnd(ctx)):
        if (sectionBreak(ctx)): continue;
        if (fileHeader(ctx)): continue;
        if (scanTune(ctx)): continue;
        if (scanDirective(ctx)): continue;
        if (comment(ctx)): continue;
        if (EOL(ctx)): continue;
        freeText(ctx);
  }
  return ctx.tokens;

  class Token:
    id: int
    line: str

