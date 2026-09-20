import json
from typing import Any

import requests

from app.schemas.ai_mapping import AIMappingRequest


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Local Ollama model
OLLAMA_MODEL = "llama3.2:3b"


# ============================================================
# OLLAMA HELPER
# ============================================================

def call_ollama(prompt: str) -> str:
    """
    Send a prompt to the local Ollama AI model.

    This does not use the OpenAI API.
    No OpenAI API key or API credits are required.
    """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2,
                },
            },
            timeout=120,
        )

    except requests.exceptions.ConnectionError as exc:
        raise ValueError(
            "Unable to connect to Ollama. "
            "Please make sure Ollama is running."
        ) from exc

    except requests.exceptions.Timeout as exc:
        raise ValueError(
            "Ollama AI request timed out. "
            "Please try again."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise ValueError(
            f"Ollama request failed: {str(exc)}"
        ) from exc

    # --------------------------------------------------------
    # CHECK HTTP RESPONSE
    # --------------------------------------------------------

    if response.status_code != 200:
        raise ValueError(
            f"Ollama returned an error: "
            f"{response.status_code} - {response.text}"
        )

    # --------------------------------------------------------
    # PARSE RESPONSE
    # --------------------------------------------------------

    try:
        response_data = response.json()

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Ollama returned an invalid response."
        ) from exc

    output = response_data.get(
        "response",
        ""
    )

    if not output:
        raise ValueError(
            "Ollama returned an empty response."
        )

    return output


# ============================================================
# BUSINESS MAPPING PROMPT
# ============================================================

def build_business_mapping_prompt(
    request: AIMappingRequest,
) -> str:

    columns_text = []

    # --------------------------------------------------------
    # BUILD COLUMN INFORMATION
    # --------------------------------------------------------

    for column in request.columns:

        details = [
            f"Name: {column.name}",
        ]

        if column.data_type:
            details.append(
                f"Data Type: {column.data_type}"
            )

        if column.nullable is not None:
            details.append(
                f"Nullable: {column.nullable}"
            )

        if column.primary_key is not None:
            details.append(
                f"Primary Key: {column.primary_key}"
            )

        columns_text.append(
            " | ".join(details)
        )

    if not columns_text:
        columns_text.append(
            "No column metadata provided."
        )

    # --------------------------------------------------------
    # BUILD RELATIONSHIP INFORMATION
    # --------------------------------------------------------

    relationships_text = []

    for relationship in request.relationships:

        parent_table = relationship.get(
            "parent_table"
        )

        parent_column = relationship.get(
            "parent_column"
        )

        child_table = relationship.get(
            "child_table"
        )

        child_column = relationship.get(
            "child_column"
        )

        if all(
            [
                parent_table,
                parent_column,
                child_table,
                child_column,
            ]
        ):
            relationships_text.append(
                f"{parent_table}.{parent_column} -> "
                f"{child_table}.{child_column}"
            )

    if not relationships_text:
        relationships_text.append(
            "No relationships provided."
        )

    # --------------------------------------------------------
    # FINAL PROMPT
    # --------------------------------------------------------

    return f"""
You are an AI database metadata mapping assistant.

Analyze the database table and determine its business meaning.

Database:
{request.database_name}

Table:
{request.table_name}

Columns:
{chr(10).join(columns_text)}

Relationships:
{chr(10).join(relationships_text)}

Generate a business mapping for this table.

Rules:

1. Business Entity must be clear and business-friendly.

2. Table Purpose must explain what the table represents.

3. AI Aliases should contain useful alternative business names.

4. Primary Identifier must be selected only when supported
   by the metadata.

5. Date Field must be selected only when a date field is
   reasonably identifiable.

6. Amount Field must be selected only when an amount or
   monetary field exists.

7. Status Field must be selected only when a status field
   exists.

8. Customer Reference must be selected only when supported.

9. Do not invent information.

10. If something cannot be determined, return null.

11. Keep descriptions concise and professional.

12. Use the actual column names when selecting fields.

13. Return ONLY valid JSON.

Return exactly this JSON structure:

{{
    "business_entity": "string",
    "table_purpose": "string",
    "ai_aliases": ["string"],
    "primary_identifier": "string or null",
    "date_field": "string or null",
    "amount_field": "string or null",
    "status_field": "string or null",
    "customer_reference": "string or null",
    "description": "string"
}}
""".strip()


# ============================================================
# COLUMN MAPPING PROMPT
# ============================================================

def build_column_mapping_prompt(
    request: AIMappingRequest,
) -> str:

    columns_text = []

    # --------------------------------------------------------
    # BUILD COLUMN INFORMATION
    # --------------------------------------------------------

    for column in request.columns:

        details = [
            f"Column Name: {column.name}",
        ]

        if column.data_type:
            details.append(
                f"Data Type: {column.data_type}"
            )

        if column.nullable is not None:
            details.append(
                f"Nullable: {column.nullable}"
            )

        if column.primary_key is not None:
            details.append(
                f"Primary Key: {column.primary_key}"
            )

        columns_text.append(
            " | ".join(details)
        )

    if not columns_text:
        columns_text.append(
            "No column metadata provided."
        )

    # --------------------------------------------------------
    # FINAL PROMPT
    # --------------------------------------------------------

    return f"""
You are an AI database metadata mapping assistant.

Analyze the columns of this database table.

Database:
{request.database_name}

Table:
{request.table_name}

Columns:
{chr(10).join(columns_text)}

For every supplied column generate:

1. Original Column Name
2. Business Name
3. Business Description
4. Business Category

Rules:

- Never change the original column name.

- Business Name must be understandable to non-technical users.

- Description must clearly explain the column.

- Business Category should describe the role of the column.

Possible categories include:

Identifier
Personal Information
Contact Information
Date
Financial
Status
Reference
Other

- Do not invent unsupported information.

- Use the table context.

- Return one result for every supplied column.

- Keep descriptions concise and professional.

- Return ONLY valid JSON.

Return exactly this structure:

{{
    "column_mappings": [
        {{
            "column_name": "original column name",
            "business_name": "business-friendly name",
            "description": "business description",
            "business_category": "category"
        }}
    ]
}}
""".strip()


# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(
    output: str,
) -> dict[str, Any]:

    output = output.strip()

    # --------------------------------------------------------
    # REMOVE MARKDOWN CODE FENCES
    # --------------------------------------------------------

    if output.startswith("```json"):
        output = output[7:]

    elif output.startswith("```"):
        output = output[3:]

    if output.endswith("```"):
        output = output[:-3]

    output = output.strip()

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:
        return json.loads(output)

    except json.JSONDecodeError as exc:
        print(
            "LOCAL AI INVALID JSON:",
            output
        )

        raise ValueError(
            "Local AI returned invalid JSON."
        ) from exc


# ============================================================
# GENERATE BUSINESS MAPPING
# ============================================================

def generate_business_mapping(
    request: AIMappingRequest,
) -> dict[str, Any]:

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    prompt = build_business_mapping_prompt(
        request
    )

    print(
        "AI BUSINESS MAPPING: "
        "Sending request to Ollama..."
    )

    # --------------------------------------------------------
    # CALL LOCAL AI
    # --------------------------------------------------------

    output = call_ollama(
        prompt
    )

    print(
        "AI BUSINESS MAPPING: "
        "Response received."
    )

    # --------------------------------------------------------
    # PARSE RESPONSE
    # --------------------------------------------------------

    result = parse_json_response(
        output
    )

    # --------------------------------------------------------
    # VALIDATE RESPONSE
    # --------------------------------------------------------

    required_fields = [
        "business_entity",
        "table_purpose",
        "ai_aliases",
        "primary_identifier",
        "date_field",
        "amount_field",
        "status_field",
        "customer_reference",
        "description",
    ]

    for field in required_fields:

        if field not in result:
            raise ValueError(
                f"Local AI response is missing "
                f"field: {field}"
            )

    # --------------------------------------------------------
    # MAKE SURE ALIASES ARE A LIST
    # --------------------------------------------------------

    if not isinstance(
        result["ai_aliases"],
        list,
    ):
        result["ai_aliases"] = [
            str(result["ai_aliases"])
        ]

    return result


# ============================================================
# GENERATE COLUMN MAPPING
# ============================================================

def generate_column_mapping(
    request: AIMappingRequest,
) -> list[dict[str, Any]]:

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    prompt = build_column_mapping_prompt(
        request
    )

    print(
        "AI COLUMN MAPPING: "
        "Sending request to Ollama..."
    )

    # --------------------------------------------------------
    # CALL LOCAL AI
    # --------------------------------------------------------

    output = call_ollama(
        prompt
    )

    print(
        "AI COLUMN MAPPING: "
        "Response received."
    )

    # --------------------------------------------------------
    # PARSE RESPONSE
    # --------------------------------------------------------

    result = parse_json_response(
        output
    )

    # --------------------------------------------------------
    # GET COLUMN MAPPINGS
    # --------------------------------------------------------

    mappings = result.get(
        "column_mappings"
    )

    if not isinstance(
        mappings,
        list,
    ):
        raise ValueError(
            "Local AI did not return valid "
            "column mappings."
        )

    if not mappings:
        raise ValueError(
            "Local AI returned no column mappings."
        )

    # --------------------------------------------------------
    # VALIDATE EACH MAPPING
    # --------------------------------------------------------

    validated_mappings = []

    for mapping in mappings:

        if not isinstance(
            mapping,
            dict,
        ):
            continue

        column_name = mapping.get(
            "column_name",
            ""
        )

        business_name = mapping.get(
            "business_name",
            ""
        )

        description = mapping.get(
            "description",
            ""
        )

        business_category = mapping.get(
            "business_category",
            "Other"
        )

        if not column_name:
            continue

        validated_mappings.append(
            {
                "column_name": column_name,
                "business_name": business_name,
                "description": description,
                "business_category": business_category,
            }
        )

    if not validated_mappings:
        raise ValueError(
            "Local AI returned no valid column mappings."
        )

    return validated_mappings