import os
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("KickAssDbgParser")

def _parse_addr(addr_str: str) -> int:
    """Robust integer/address parsing for hex or decimal strings."""
    addr_str = addr_str.strip()
    if addr_str.startswith("$"):
        return int(addr_str[1:], 16)
    if addr_str.lower().startswith("0x"):
        return int(addr_str[2:], 16)
    try:
        return int(addr_str, 16) if any(c in "abcdefABCDEF" for c in addr_str) else int(addr_str, 10)
    except ValueError:
        return int(addr_str, 16)

class KickAssDbgParser:
    """
    Parser for KickAssembler XML debug (.dbg) files.
    Allows mapping Commodore 64 machine addresses to original source file lines and vice-versa.
    """
    def __init__(self) -> None:
        self.sources: Dict[int, Dict[str, str]] = {}  # file_id -> {"filepath": ..., "filename": ...}
        self.addr_to_source: Dict[int, Tuple[int, int]] = {}  # address -> (file_id, line_number)
        self.source_to_addr: Dict[Tuple[int, int], int] = {}  # (file_id, line_number) -> address
        self.labels: Dict[str, int] = {}  # label_name -> address
        self.loaded_filepath: Optional[str] = None

    def clear(self) -> None:
        self.sources.clear()
        self.addr_to_source.clear()
        self.source_to_addr.clear()
        self.labels.clear()
        self.loaded_filepath = None

    def load_dbg(self, filepath: str) -> bool:
        """
        Parses the KickAssembler XML .dbg file.
        Returns True if parsed successfully.
        """
        if not os.path.exists(filepath):
            logger.error(f"Debug file not found: {filepath}")
            raise FileNotFoundError(f"Debug file not found: {filepath}")

        self.clear()
        self.loaded_filepath = filepath

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # 1. Parse sources
            sources_node = root.find("sources")
            if sources_node is not None:
                for src in sources_node.findall("source"):
                    src_id_str = src.attrib.get("id")
                    if src_id_str is not None:
                        src_id = int(src_id_str)
                        path = src.attrib.get("filepath", "")
                        name = src.attrib.get("filename", "")
                        if not name and path:
                            name = os.path.basename(path)
                        self.sources[src_id] = {"filepath": path, "filename": name}

            # 2. Parse sourceinfo (lines)
            sourceinfo_node = root.find("sourceinfo")
            if sourceinfo_node is not None:
                for line_node in sourceinfo_node.findall("line"):
                    file_id_str = line_node.attrib.get("fileid")
                    line_num_str = line_node.attrib.get("line")

                    start_str = line_node.attrib.get("startaddress") or line_node.attrib.get("startadd") or line_node.attrib.get("start")
                    end_str = line_node.attrib.get("endaddress") or line_node.attrib.get("endadd") or line_node.attrib.get("end")

                    if file_id_str is not None and line_num_str is not None and start_str is not None:
                        file_id = int(file_id_str)
                        line_num = int(line_num_str)
                        start_addr = _parse_addr(start_str)
                        end_addr = _parse_addr(end_str) if end_str else start_addr

                        for addr in range(start_addr, end_addr + 1):
                            self.addr_to_source[addr] = (file_id, line_num)

                        self.source_to_addr[(file_id, line_num)] = start_addr

            # 3. Parse labels (optional)
            labels_node = root.find("labels")
            if labels_node is not None:
                for label_node in labels_node.findall("label"):
                    name = label_node.attrib.get("name")
                    addr_str = label_node.attrib.get("address") or label_node.attrib.get("addr") or label_node.attrib.get("val")
                    if name and addr_str:
                        addr = _parse_addr(addr_str)
                        self.labels[name] = addr

            logger.info(f"Loaded debug file '{filepath}': {len(self.sources)} sources, {len(self.addr_to_source)} mapped address bytes.")
            return True
        except Exception as e:
            logger.error(f"Error loading debug file '{filepath}': {e}")
            raise

    def get_source_line(self, address: int) -> Optional[Tuple[str, int]]:
        """
        Given a machine address, return (source_filepath, line_number).
        """
        mapping = self.addr_to_source.get(address & 0xFFFF)
        if not mapping:
            return None
        file_id, line_num = mapping
        src_info = self.sources.get(file_id)
        if not src_info:
            return None
        return src_info["filepath"], line_num

    def get_address_for_line(self, filename_or_path: str, line_num: int) -> Optional[int]:
        """
        Given a source filename/path and a line number, return the starting machine address.
        """
        file_id: Optional[int] = None
        target = filename_or_path.lower()
        for fid, s_info in self.sources.items():
            if s_info["filepath"].lower() == target or s_info["filename"].lower() == target or os.path.basename(s_info["filepath"]).lower() == target:
                file_id = fid
                break

        if file_id is None:
            return None

        return self.source_to_addr.get((file_id, line_num))
