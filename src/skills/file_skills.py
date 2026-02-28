"""
文件处理技能集 - 用于文件读写和处理
"""


def read_large_file(file_path: str, start_line: int = 0, num_lines: int = 200) -> str:
    """
    Read a subset of lines from a large text file to avoid size limits
    Args:
        file_path: Path to the file to read
        start_line: Line number to start reading from (0-indexed)
        num_lines: Number of lines to read
    Returns:
        String content of the requested lines
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    end_line = min(start_line + num_lines, len(lines))
    return ''.join(lines[start_line:end_line])
