"""
Prompt construction utilities for MediAssist AI.

This module centralizes all string templates used to interact with
language models.  Keeping prompts in one place makes it easy to
iterate on the wording and to support multiple languages.  The
functions defined here accept report text, abnormal findings, and
other contextual information, and produce a formatted prompt that
conveys the required instructions to the LLM.
"""

from __future__ import annotations

from typing import Iterable, List

from .models import DetectedParameter


def _format_abnormal_items(abnormal_items: Iterable[DetectedParameter], language: str) -> str:
    """Format the list of abnormal parameters for inclusion in prompts.

    If no abnormal items are present, a generic phrase is returned.
    Otherwise, each item is listed on its own line with the value and
    reference range.  For Bangla, headings are translated.
    """
    if not abnormal_items:
        return "No obviously abnormal values were detected."
    lines: List[str] = []
    header = "Likely Abnormal Parameters:" if language.lower().startswith("en") else "সম্ভাব্য অস্বাভাবিক মান:"
    lines.append(header)
    for item in abnormal_items:
        name = item.name
        value = item.value
        ref = item.reference_range
        status = item.status
        if language.lower().startswith("en"):
            line = f"- {name}: {value} (reference {ref}, appears {status})"
        else:
            # Simple Bangla translation; for production you would
            # translate terms properly or use a translation API.
            status_bn = {
                "low": "কম",
                "normal": "স্বাভাবিক",
                "high": "উচ্চ",
            }.get(status.lower(), status)
            line = f"- {name}: {value} (রেফারেন্স {ref}, মনে হচ্ছে {status_bn})"
        lines.append(line)
    return "\n".join(lines)


def build_medical_explain_prompt(report_text: str, language: str, abnormal_items: Iterable[DetectedParameter]) -> str:
    """Construct a prompt instructing the LLM to explain a medical report.

    The prompt tells the model to act as a friendly medical report
    explainer.  It provides the raw report text, a list of abnormal
    findings, and clear instructions about tone and safety.  The
    ``language`` parameter controls whether the explanation should be
    delivered in English or Bangla.
    """
    abnormal_section = _format_abnormal_items(abnormal_items, language)
    disclaimer_en = (
        "This explanation is for educational purposes only and does not "
        "constitute medical advice. Always consult a licensed doctor for "
        "diagnosis or treatment."
    )
    disclaimer_bn = (
        "এই ব্যাখ্যাটি শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে। চিকিৎসা সংক্রান্ত সিদ্ধান্তের জন্য "
        "সর্বদা যোগ্য ডাক্তারের পরামর্শ নিন।"
    )
    disclaimer = disclaimer_en if language.lower().startswith("en") else disclaimer_bn

    if language.lower().startswith("en"):
        intro = (
            "You are a helpful assistant tasked with explaining a patient's medical report "
            "in simple, non‑technical language. Do not provide a diagnosis or recommend treatments. "
            "Base your explanation solely on the provided report text."
        )
        sections = (
            "Provide a concise summary, highlight the important findings, explain any abnormal values in simple terms, "
            "suggest questions the patient could ask their doctor, and finish with a disclaimer."
        )
    else:
        intro = (
            "তুমি একজন সহায়ক সহকারী, যার কাজ রোগীর মেডিকেল রিপোর্টটি সাধারণ ও সহজ ভাষায় ব্যাখ্যা করা। "
            "কোনও রোগ নির্ণয় বা চিকিৎসার সুপারিশ করবে না। শুধু প্রদত্ত রিপোর্টের উপর ভিত্তি করে ব্যাখ্যা দাও।"
        )
        sections = (
            "সংক্ষিপ্ত সারাংশ দাও, গুরুত্বপূর্ণ ফলাফল উল্লেখ কর, অস্বাভাবিক মানগুলোর সহজ ব্যাখ্যা দাও, "
            "ডাক্তারের কাছে কী প্রশ্ন করা যায় তা পরামর্শ দাও এবং শেষে একটি সতর্কবার্তা দাও।"
        )

    prompt = (
        f"{intro}\n\n"
        f"Report Text:\n{report_text}\n\n"
        f"{abnormal_section}\n\n"
        f"{sections}\n\n"
        f"Disclaimer: {disclaimer}"
    )
    return prompt


def build_report_qa_prompt(report_text: str, question: str, language: str) -> str:
    """Construct a prompt for answering a follow‑up question about the report.

    The prompt instructs the model to answer the user's question using
    information from the report and general medical knowledge.  It
    reminds the model not to diagnose or prescribe.  The answer will be
    returned in the requested language.
    """
    disclaimer_en = (
        "This answer is for educational purposes only and does not constitute medical advice. "
        "Always consult a licensed doctor for diagnosis or treatment."
    )
    disclaimer_bn = (
        "এই উত্তরটি শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে। চিকিৎসা সংক্রান্ত সিদ্ধান্তের জন্য "
        "সর্বদা যোগ্য ডাক্তারের পরামর্শ নিন।"
    )
    disclaimer = disclaimer_en if language.lower().startswith("en") else disclaimer_bn
    if language.lower().startswith("en"):
        prompt = (
            "You are a helpful assistant answering a patient's question about their medical report. "
            "Use only the information in the report and general educational explanations. "
            "Do not provide a diagnosis or recommend treatments.\n\n"
            f"Report Text:\n{report_text}\n\n"
            f"Question: {question}\n\n"
            "Answer in simple English and include a brief disclaimer at the end.\n\n"
            f"Disclaimer: {disclaimer}"
        )
    else:
        prompt = (
            "তুমি একজন সহায়ক সহকারী, যে রোগীর মেডিকেল রিপোর্ট সম্পর্কিত প্রশ্নের উত্তর দেবে। "
            "শুধু রিপোর্টে থাকা তথ্য ও সাধারণ শিক্ষামূলক ব্যাখ্যা ব্যবহার করো। কোনও রোগ নির্ণয় বা চিকিৎসা পরামর্শ দেবে না।\n\n"
            f"রিপোর্টের লেখা:\n{report_text}\n\n"
            f"প্রশ্ন: {question}\n\n"
            "সহজ বাংলায় উত্তর দাও এবং শেষে একটি সতর্কবার্তা যোগ করো।\n\n"
            f"সতর্কতা: {disclaimer}"
        )
    return prompt
