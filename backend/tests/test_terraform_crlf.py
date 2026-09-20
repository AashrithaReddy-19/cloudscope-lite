import pytest
from app.services.terraform_parser import normalize_terraform_text,parse_terraform,validate_upload,TerraformParseError

FIXTURE_LF="""resource "aws_instance" "web_server" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
  }

  tags = {
    Name = "cloudscope-demo-web"
  }
}

resource "aws_ebs_volume" "application_data" {
  availability_zone = "us-east-1a"
  type              = "gp3"
  size              = 20
}

resource "aws_s3_bucket" "application_files" {
  bucket = "cloudscope-simulation-example"
}

resource "aws_db_instance" "application_database" {
  identifier          = "cloudscope-simulation-db"
  engine              = "mysql"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  storage_type        = "gp3"
  multi_az            = false
  publicly_accessible = false
}
"""
FIXTURE_CRLF=FIXTURE_LF.replace("\n","\r\n")
FIXTURE_CR=FIXTURE_LF.replace("\n","\r")
FIXTURE_BOM_CRLF="﻿"+FIXTURE_CRLF

def _assert_fixture_parsed(result):
    resources={r["resource_name"]:r for r in result["resources"]}
    assert set(resources)=={"web_server","application_data","application_files","application_database"}
    assert not result["unsupported_warnings"]
    web=resources["web_server"]
    assert web["attributes"]["ami"]=="ami-12345678"
    assert web["attributes"]["instance_type"]=="t3.micro"
    db=resources["application_database"]
    assert db["attributes"]["multi_az"] is False
    assert db["attributes"]["publicly_accessible"] is False
    assert db["attributes"]["allocated_storage"]==20

def test_normalize_strips_bom():
    assert normalize_terraform_text("﻿resource")=="resource"
def test_normalize_converts_crlf():
    assert normalize_terraform_text("a\r\nb")=="a\nb"
def test_normalize_converts_standalone_cr():
    assert normalize_terraform_text("a\rb")=="a\nb"
def test_normalize_leaves_lf_untouched():
    assert normalize_terraform_text("a\nb")=="a\nb"
def test_normalize_does_not_collapse_whitespace():
    assert normalize_terraform_text("a\r\n\r\nb")=="a\n\nb"
def test_normalize_preserves_quoted_value_content():
    assert normalize_terraform_text('x = "a  b\tc"')=='x = "a  b\tc"'

# 1. Valid LF Terraform
def test_lf_fixture_parses():
    _assert_fixture_parsed(parse_terraform(FIXTURE_LF))
# 2. Same configuration using CRLF (the reported production bug)
def test_crlf_fixture_parses_identically():
    _assert_fixture_parsed(parse_terraform(FIXTURE_CRLF))
# 3. Same configuration using standalone CR
def test_cr_fixture_parses_identically():
    _assert_fixture_parsed(parse_terraform(FIXTURE_CR))
# 4. UTF-8 BOM plus CRLF
def test_bom_crlf_fixture_parses():
    _assert_fixture_parsed(parse_terraform(FIXTURE_BOM_CRLF))
# 7/8/9/10 (nested root_block_device, tags map, booleans, multiple resources) are all
# exercised by the fixture assertions above.

# 11. Malformed Terraform still returns a safe validation error (not a crash), CRLF included
def test_malformed_crlf_terraform_raises_parse_error():
    with pytest.raises(TerraformParseError):
        parse_terraform('resource "aws_instance" "x" {\r\n'.replace("\n","\r\n"))

# 12. Binary input remains rejected
def test_binary_upload_still_rejected():
    with pytest.raises(TerraformParseError):
        validate_upload("main.tf", b"\x00binary")
# 13. Oversized input remains rejected
def test_oversized_upload_still_rejected():
    with pytest.raises(TerraformParseError):
        validate_upload("main.tf", b"a"*(1024*1024+1))

# 14. Unsupported resources still produce warnings, even through CRLF text
def test_unsupported_resource_warning_survives_crlf():
    text='resource "aws_lambda_function" "x" {\r\n  runtime = "python3.13"\r\n}\r\n'
    result=parse_terraform(text)
    assert result["unsupported_warnings"]
    assert "aws_lambda_function" in result["unsupported_warnings"][0]

# 15. Terraform input is parsed but never executed
def test_parser_module_never_imports_execution_primitives():
    import app.services.terraform_parser as mod,inspect
    source=inspect.getsource(mod)
    for forbidden in ("subprocess","os.system","exec(","eval("):
        assert forbidden not in source
def test_suspicious_string_value_is_returned_as_inert_data_not_executed():
    text='resource "aws_s3_bucket" "x" { bucket = "; rm -rf / #" }'
    result=parse_terraform(text)
    assert result["resources"][0]["attributes"]["bucket"]=="; rm -rf / #"
