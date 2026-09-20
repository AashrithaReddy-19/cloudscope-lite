import io
import re
from pathlib import PurePath
import hcl2

SUPPORTED = {"aws_instance", "aws_ebs_volume", "aws_s3_bucket", "aws_db_instance"}

class TerraformParseError(ValueError): pass

def validate_upload(filename: str, content: bytes) -> str:
    if PurePath(filename).suffix.lower() != ".tf": raise TerraformParseError("Only .tf files are accepted.")
    if len(content) > 1024 * 1024: raise TerraformParseError("Terraform file exceeds the 1 MB limit.")
    if b"\x00" in content: raise TerraformParseError("Binary content is not accepted.")
    try: return content.decode("utf-8")
    except UnicodeDecodeError as exc: raise TerraformParseError("File must be UTF-8 text.") from exc

def normalize_terraform_text(text: str) -> str:
    if text.startswith("﻿"): text = text.removeprefix("﻿")
    return text.replace("\r\n", "\n").replace("\r", "\n")

def _resolve(value, variables, field, warnings):
    if isinstance(value, str):
        match = re.fullmatch(r"\$\{var\.([\w-]+)\}", value)
        if match:
            if match.group(1) in variables: return variables[match.group(1)]
            warnings.append({"field": field, "message": "The value could not be resolved. A default value is required for cost estimation."})
            return None
        if "${" in value:
            warnings.append({"field": field, "message": "Expression could not be resolved."}); return None
    return value

def parse_terraform(text: str, region="us-east-1"):
    text = normalize_terraform_text(text)
    try: document = hcl2.load(io.StringIO(text))
    except Exception as exc: raise TerraformParseError(f"Malformed Terraform: {exc}") from exc
    variables = {}
    for block in document.get("variable", []):
        for name, body in block.items():
            if "default" in body: variables[name] = body["default"]
    resources, unsupported = [], []
    for block in document.get("resource", []):
        for kind, named in block.items():
            for name, attrs in named.items():
                if kind not in SUPPORTED: unsupported.append(f"Unsupported resource: {kind}.{name}"); continue
                warnings=[]; normalized={k:_resolve(v, variables, k, warnings) for k,v in attrs.items() if isinstance(v,(str,int,float,bool))}
                resources.append({"resource_type":kind,"resource_name":name,"region":region,"attributes":normalized,"warnings":warnings})
    return {"resources": resources, "unsupported_warnings": unsupported}

