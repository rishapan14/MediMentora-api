"""OpenAI-powered medical report analysis."""

import json

from flask import current_app


class AIAnalysisService:
  """Send report text to OpenAI and parse structured analysis."""

  SYSTEM_PROMPT = (
    "You are a clinical education assistant for nurses and medical students. "
    "Analyze the provided medical report and respond ONLY with valid JSON using this schema:\n"
    "{\n"
    '  "simple_explanation": "plain language summary",\n'
    '  "abnormal_values": [{"name": "", "value": "", "normal_range": "", "significance": ""}],\n'
    '  "possible_diseases": [{"disease": "", "likelihood": "low|medium|high", "reasoning": ""}],\n'
    '  "medical_terms": [{"term": "", "explanation": ""}],\n'
    '  "learning_topics": ["topic1", "topic2"]\n'
    "}\n"
    "Do not include markdown or extra text outside the JSON."
  )

  @classmethod
  def analyze_report(cls, report_text):
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
      return cls._mock_analysis(report_text)

    try:
      from openai import OpenAI
    except ImportError:
      raise RuntimeError("openai package is required for AI analysis.")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
      model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
      messages=[
        {"role": "system", "content": cls.SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze this medical report:\n\n{report_text}"},
      ],
      temperature=0.3,
      response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return json.loads(content)

  @staticmethod
  def _mock_analysis(report_text):
    """Fallback when OpenAI key is not configured (development/demo)."""
    preview = (report_text or "")[:200]
    return {
      "simple_explanation": (
        "This is a demo analysis. Configure OPENAI_API_KEY for real AI insights. "
        f"Report preview: {preview}..."
      ),
      "abnormal_values": [
        {
          "name": "Hemoglobin",
          "value": "10.2 g/dL",
          "normal_range": "12-16 g/dL",
          "significance": "Below normal — possible anemia",
        }
      ],
      "possible_diseases": [
        {
          "disease": "Iron deficiency anemia",
          "likelihood": "medium",
          "reasoning": "Low hemoglobin is a common indicator.",
        }
      ],
      "medical_terms": [
        {"term": "Hemoglobin", "explanation": "Protein in red blood cells that carries oxygen."}
      ],
      "learning_topics": ["Anemia", "CBC interpretation", "Nursing assessment"],
    }

  @classmethod
  def simulation_feedback(cls, scenario, diagnosis, treatment, correct_diagnosis, correct_treatment):
    """Generate immediate AI feedback for simulation attempts."""
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
      score = 0
      if diagnosis and diagnosis.lower() == correct_diagnosis.lower():
        score += 50
      if treatment and treatment.lower() == correct_treatment.lower():
        score += 50
      return {
        "feedback": (
          f"Demo feedback: Your diagnosis was {'correct' if score >= 50 else 'incorrect'}. "
          f"Correct diagnosis: {correct_diagnosis}. Correct treatment: {correct_treatment}."
        ),
        "score": score,
      }

    try:
      from openai import OpenAI
    except ImportError:
      raise RuntimeError("openai package is required.")

    client = OpenAI(api_key=api_key)
    prompt = (
      f"Patient scenario: {scenario}\n"
      f"Student diagnosis: {diagnosis}\n"
      f"Student treatment: {treatment}\n"
      f"Correct diagnosis: {correct_diagnosis}\n"
      f"Correct treatment: {correct_treatment}\n\n"
      "Provide constructive clinical feedback and a score 0-100 as JSON: "
      '{"feedback": "...", "score": 85}'
    )
    response = client.chat.completions.create(
      model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
      messages=[{"role": "user", "content": prompt}],
      temperature=0.4,
      response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
