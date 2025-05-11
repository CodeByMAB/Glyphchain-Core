"""
Utility functions for Glyphchain operations including hashing, export, and timestamping.
"""

import json
import hashlib
import zipfile
import os
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, Tuple


def generate_glyph_hash(glyph_data: Dict[str, Any]) -> str:
    """
    Generate a SHA-256 hash from a glyph object's data.
    
    Args:
        glyph_data: Dictionary containing the glyph's data
        
    Returns:
        str: Hexadecimal SHA-256 hash of the glyph data
    """
    # Sort keys to ensure consistent hashing
    encoded = json.dumps(glyph_data, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def export_glyph_bundle(
    glyph_path: str,
    echo_log_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Create a ZIP bundle containing the glyph manifest and optional echo log.
    
    Args:
        glyph_path: Path to the glyph manifest JSON file
        echo_log_path: Optional path to the echo log JSON file
        output_path: Optional path for the output ZIP file
        
    Returns:
        str: Path to the created ZIP bundle
        
    Raises:
        FileNotFoundError: If glyph manifest or echo log file doesn't exist
    """
    if not os.path.exists(glyph_path):
        raise FileNotFoundError(f"Glyph manifest not found: {glyph_path}")
    
    if echo_log_path and not os.path.exists(echo_log_path):
        raise FileNotFoundError(f"Echo log not found: {echo_log_path}")
    
    if not output_path:
        base_name = os.path.splitext(os.path.basename(glyph_path))[0]
        output_path = f"{base_name}_bundle.zip"
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add glyph manifest
        zipf.write(glyph_path, os.path.basename(glyph_path))
        
        # Add echo log if provided
        if echo_log_path:
            zipf.write(echo_log_path, os.path.basename(echo_log_path))
    
    return output_path


def check_ots_installed() -> bool:
    """
    Check if OpenTimestamps CLI is installed and available.
    
    Returns:
        bool: True if ots command is available, False otherwise
    """
    try:
        subprocess.run(['ots', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def timestamp_glyph(
    glyph_path: str,
    server: str = "https://a.pool.opentimestamps.org"
) -> Tuple[str, str]:
    """
    Create an OpenTimestamps proof for a glyph manifest using ots CLI.
    
    Args:
        glyph_path: Path to the glyph manifest JSON file
        server: OpenTimestamps server URL
        
    Returns:
        Tuple[str, str]: Path to the .ots file and the timestamp hash
        
    Raises:
        FileNotFoundError: If glyph manifest doesn't exist
        RuntimeError: If ots command fails
    """
    if not check_ots_installed():
        raise RuntimeError("OpenTimestamps CLI not found. Install with: pip install opentimestamps-client")
    
    if not os.path.exists(glyph_path):
        raise FileNotFoundError(f"Glyph manifest not found: {glyph_path}")
    
    # Create .ots file
    ots_path = f"{os.path.splitext(glyph_path)[0]}.ots"
    
    try:
        # Run ots stamp command with 30 min timeout and 2 attestations
        result = subprocess.run(
            ['ots', 'stamp', '--timeout', '1800', '-m', '2', glyph_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract hash from output
        hash_line = [line for line in result.stdout.split('\n') if 'Hash' in line]
        if hash_line:
            timestamp_hash = hash_line[0].split(': ')[1].strip()
        else:
            timestamp_hash = "Unknown"
        
        return ots_path, timestamp_hash
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"OpenTimestamps stamping failed: {e.stderr}")


def verify_glyph_timestamp(
    glyph_path: str,
    ots_path: str,
    server: str = "https://a.pool.opentimestamps.org"
) -> Tuple[bool, str]:
    """
    Verify an OpenTimestamps proof for a glyph manifest using ots CLI.
    
    Args:
        glyph_path: Path to the glyph manifest JSON file
        ots_path: Path to the .ots proof file
        server: OpenTimestamps server URL
        
    Returns:
        Tuple[bool, str]: (verification success, verification message)
        
    Raises:
        FileNotFoundError: If glyph manifest or .ots file doesn't exist
        RuntimeError: If ots command fails
    """
    if not check_ots_installed():
        raise RuntimeError("OpenTimestamps CLI not found. Install with: pip install opentimestamps-client")
    
    if not os.path.exists(glyph_path):
        raise FileNotFoundError(f"Glyph manifest not found: {glyph_path}")
    
    if not os.path.exists(ots_path):
        raise FileNotFoundError(f"OTS proof not found: {ots_path}")
    
    try:
        # Run ots verify command with correct syntax
        result = subprocess.run(
            ['ots', 'verify', ots_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if verification was successful
        success = "Success! Bitcoin block" in result.stdout
        return success, result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip() 