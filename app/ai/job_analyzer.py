"""
Job Analyzer - Extracts structured requirements and analyzes candidate fit

This module provides functions to:
1. Extract specific experience requirements from job descriptions
2. Extract required and preferred skills
3. Extract education, certification, and clearance requirements
4. Analyze gaps between candidate resume and job requirements
5. Create tech stack overlap analysis
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


def extract_structured_requirements(job_description: str) -> Dict[str, Any]:
    """
    Extract all structured requirements from a job description.

    Returns a comprehensive dictionary with:
    - experience: List of experience requirements with years
    - education: List of education requirements
    - certifications: List of required/preferred certifications
    - clearance: Security clearance requirements
    - skills_required: List of required technical skills
    - skills_preferred: List of preferred/nice-to-have skills
    - responsibilities: Key job responsibilities
    """
    if not job_description:
        return {}

    text = job_description
    text_lower = text.lower()

    result = {
        "experience": [],
        "education": [],
        "certifications": [],
        "clearance": None,
        "skills_required": [],
        "skills_preferred": [],
        "responsibilities": [],
    }

    # ===== EXPERIENCE REQUIREMENTS =====
    experience_patterns = [
        # "5+ years of AWS experience"
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+)?(?:with|in|of)?\s*([A-Za-z0-9\s\.\+\#\/\-]+?)(?:\s+experience)?(?:[,\.\n]|$)",
            "years_skill",
        ),
        # "Bachelor's and 2 years experience"
        (
            r"(?:bachelor'?s?|master'?s?|phd)\s+(?:degree\s+)?(?:and|with)\s+(\d+)\+?\s*(?:years?|yrs?)",
            "edu_years",
        ),
        # "minimum 5 years"
        (
            r"(?:minimum|at\s+least|min)\s+(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?([A-Za-z0-9\s\.\+\#\/\-]+?)(?:\s+experience)?",
            "min_years",
        ),
        # "5-7 years of experience"
        (
            r"(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+)?(?:with|in)?\s*([A-Za-z0-9\s\.\+\#\/\-]+)?",
            "range",
        ),
    ]

    seen_exp = set()
    for pattern, ptype in experience_patterns:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            groups = match.groups()
            exp_item = {}

            if ptype == "years_skill" and len(groups) >= 2:
                years = int(groups[0])
                skill = groups[1].strip()
                if skill and len(skill) > 2 and len(skill) < 50:
                    exp_item = {"years": years, "skill": skill.title(), "type": "specific"}
            elif ptype == "min_years" and len(groups) >= 2:
                years = int(groups[0])
                skill = groups[1].strip() if groups[1] else "general"
                exp_item = {"years": years, "skill": skill.title(), "type": "minimum"}
            elif ptype == "range" and len(groups) >= 2:
                years_min = int(groups[0])
                years_max = int(groups[1])
                skill = groups[2].strip() if len(groups) > 2 and groups[2] else "general experience"
                exp_item = {
                    "years": years_min,
                    "years_max": years_max,
                    "skill": skill.title(),
                    "type": "range",
                }

            if exp_item and exp_item.get("skill"):
                key = f"{exp_item.get('years', 0)}_{exp_item.get('skill', '').lower()[:20]}"
                if key not in seen_exp:
                    seen_exp.add(key)
                    result["experience"].append(exp_item)

    # ===== EDUCATION REQUIREMENTS =====
    education_patterns = [
        (
            r"(?:bachelor'?s?|bs|ba|b\.s\.|b\.a\.)\s*(?:degree)?\s*(?:in)?\s*([A-Za-z\s]+)?",
            "bachelor",
        ),
        (
            r"(?:master'?s?|ms|ma|m\.s\.|m\.a\.|mba)\s*(?:degree)?\s*(?:in)?\s*([A-Za-z\s]+)?",
            "master",
        ),
        (r"(?:ph\.?d\.?|doctorate)\s*(?:degree)?\s*(?:in)?\s*([A-Za-z\s]+)?", "phd"),
        (r"(?:associate'?s?|as|aa)\s*(?:degree)?\s*(?:in)?\s*([A-Za-z\s]+)?", "associate"),
    ]

    edu_levels = {"phd": 4, "master": 3, "bachelor": 2, "associate": 1}
    seen_edu = set()

    for pattern, level in education_patterns:
        for match in re.finditer(pattern, text_lower):
            field = match.group(1).strip() if match.group(1) else ""
            field = re.sub(
                r"\s*(or|and|with|required|preferred).*", "", field, flags=re.IGNORECASE
            ).strip()
            if len(field) > 50:
                field = ""
            edu_key = level
            if edu_key not in seen_edu:
                seen_edu.add(edu_key)
                result["education"].append(
                    {
                        "level": level.title(),
                        "field": field.title() if field else None,
                        "priority": edu_levels.get(level, 0),
                    }
                )

    # Sort by priority
    result["education"].sort(key=lambda x: x.get("priority", 0), reverse=True)

    # ===== CERTIFICATIONS =====
    cert_patterns = [
        r"(AWS\s+(?:Solutions?\s+Architect|SysOps\s+Administrator|Developer|DevOps\s+Engineer|Cloud\s+Practitioner)(?:\s+(?:Associate|Professional))?)",
        r"(Azure\s+(?:Administrator|Developer|Solutions?\s+Architect|DevOps\s+Engineer)(?:\s+(?:Associate|Expert))?)",
        r"(GCP\s+(?:Cloud\s+Architect|Cloud\s+Engineer|Data\s+Engineer))",
        r"(Certified\s+Kubernetes\s+Administrator|CKA)",
        r"(Certified\s+Kubernetes\s+(?:Application\s+Developer|Security\s+Specialist)|CKAD|CKS)",
        r"(CompTIA\s+(?:Security\+|Network\+|A\+|Cloud\+|Linux\+))",
        r"(Security\+|Sec\+)",
        r"(CISSP|CISM|CEH|OSCP)",
        r"(PMP|Scrum\s+Master|CSM|SAFe\s+Agilist)",
        r"(Terraform\s+(?:Associate|Professional))",
        r"(CCNA|CCNP|CCIE)",
    ]

    seen_certs = set()
    for pattern in cert_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            cert = match.group(1).strip()
            cert_lower = cert.lower()
            if cert_lower not in seen_certs:
                seen_certs.add(cert_lower)
                # Determine if required or preferred
                context_start = max(0, match.start() - 100)
                context = text_lower[context_start : match.end() + 50]
                is_required = any(w in context for w in ["required", "must have", "mandatory"])
                result["certifications"].append({"name": cert, "required": is_required})

    # ===== SECURITY CLEARANCE =====
    clearance_patterns = [
        (r"(TS/SCI|Top\s+Secret/SCI)", "TS/SCI"),
        (r"(Top\s+Secret)", "Top Secret"),
        (r"(Secret\s+clearance)", "Secret"),
        (r"(Public\s+Trust)", "Public Trust"),
    ]

    for pattern, level in clearance_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            context = text_lower
            must_obtain = (
                "able to obtain" in context or "must obtain" in context or "eligibility" in context
            )
            result["clearance"] = {
                "level": level,
                "must_obtain": must_obtain,
                "current_required": not must_obtain,
            }
            break

    # ===== TECHNICAL SKILLS =====
    # Use the existing TECH_SKILLS dictionary for skill extraction
    all_skills = extract_all_skills_from_text(job_description)

    # Try to separate required vs preferred based on context
    required_section_match = re.search(
        r"(?:required|must\s+have|minimum|essential)[\s\w]*(?:qualifications?|requirements?|skills?)?:?\s*([\s\S]*?)(?=(?:preferred|nice|bonus|desired|about\s+us|\n\n\n|benefits|$))",
        text_lower,
        re.IGNORECASE,
    )
    preferred_section_match = re.search(
        r"(?:preferred|nice\s+to\s+have|bonus|desired)[\s\w]*(?:qualifications?|requirements?|skills?)?:?\s*([\s\S]*?)(?=(?:about\s+us|\n\n\n|benefits|equal\s+opportunity|$))",
        text_lower,
        re.IGNORECASE,
    )

    if required_section_match:
        required_skills = extract_all_skills_from_text(required_section_match.group(1))
        for skills in required_skills.values():
            result["skills_required"].extend(
                [s.title() if len(s) > 3 else s.upper() for s in skills]
            )

    if preferred_section_match:
        preferred_skills = extract_all_skills_from_text(preferred_section_match.group(1))
        for skills in preferred_skills.values():
            s_list = [s.title() if len(s) > 3 else s.upper() for s in skills]
            result["skills_preferred"].extend(
                [s for s in s_list if s not in result["skills_required"]]
            )

    # If no sections found, put all skills as required
    if not result["skills_required"] and not result["skills_preferred"]:
        for skills in all_skills.values():
            result["skills_required"].extend(
                [s.title() if len(s) > 3 else s.upper() for s in skills]
            )

    # Dedupe
    result["skills_required"] = list(dict.fromkeys(result["skills_required"]))
    result["skills_preferred"] = list(dict.fromkeys(result["skills_preferred"]))

    # ===== RESPONSIBILITIES (first few bullet points) =====
    resp_patterns = [
        r"(?:responsibilities|duties|what\s+you(?:'ll)?\s+do)[\s:]*\n((?:[\s]*[-•*]\s*[^\n]+\n?){1,10})",
        r"(?:as\s+a\s+\w+,?\s+you\s+will)[\s:]*\n((?:[\s]*[-•*]\s*[^\n]+\n?){1,10})",
    ]

    for pattern in resp_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            bullets = re.findall(r"[-•*]\s*([^\n]+)", match.group(1))
            result["responsibilities"] = [
                b.strip().capitalize() for b in bullets[:8] if len(b) > 10
            ]
            break

    return result


def match_requirements_to_resume(requirements: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
    """
    Match extracted requirements against a resume to show what the candidate has vs lacks.

    Returns:
    - matched: Requirements the candidate appears to meet
    - missing: Requirements the candidate appears to lack
    - match_summary: Quick summary stats
    """
    if not requirements or not resume_text:
        return {"matched": [], "missing": [], "match_summary": {}}

    resume_lower = resume_text.lower()
    matched = []
    missing = []

    # Check experience requirements
    for exp in requirements.get("experience", []):
        skill_lower = exp.get("skill", "").lower()
        years = exp.get("years", 0)

        # Check if skill is in resume
        skill_in_resume = any(
            s in resume_lower
            for s in [skill_lower, skill_lower.replace(" ", ""), skill_lower.replace("-", " ")]
        )

        item = {
            "type": "experience",
            "description": f"{years}+ years of {exp.get('skill', 'experience')}",
            "years": years,
            "skill": exp.get("skill"),
        }

        if skill_in_resume:
            matched.append(item)
        else:
            missing.append(item)

    # Check education
    edu_in_resume = {
        "bachelor": any(w in resume_lower for w in ["bachelor", "b.s.", "b.a.", "bs ", "ba "]),
        "master": any(w in resume_lower for w in ["master", "m.s.", "m.a.", "ms ", "ma ", "mba"]),
        "phd": any(w in resume_lower for w in ["ph.d", "phd", "doctorate"]),
    }

    for edu in requirements.get("education", []):
        level = edu.get("level", "").lower()
        item = {
            "type": "education",
            "description": f"{edu.get('level', '')} degree"
            + (f" in {edu.get('field')}" if edu.get("field") else ""),
            "level": edu.get("level"),
        }
        if edu_in_resume.get(level, False):
            matched.append(item)
        else:
            missing.append(item)

    # Check certifications
    for cert in requirements.get("certifications", []):
        cert_name = cert.get("name", "")
        cert_lower = cert_name.lower()
        # Check for cert or common abbreviations
        has_cert = cert_lower in resume_lower or any(
            abbrev in resume_lower
            for abbrev in [
                cert_lower.replace(" ", ""),
                cert_lower.split()[0] if " " in cert_lower else "",
            ]
        )

        item = {
            "type": "certification",
            "description": cert_name,
            "required": cert.get("required", False),
        }

        if has_cert:
            matched.append(item)
        else:
            missing.append(item)

    # Check clearance
    clearance = requirements.get("clearance")
    if clearance:
        clearance_terms = ["clearance", "secret", "ts/sci", "public trust"]
        has_clearance = any(term in resume_lower for term in clearance_terms)

        item = {
            "type": "clearance",
            "description": f"{clearance.get('level', '')} clearance",
            "level": clearance.get("level"),
            "must_obtain": clearance.get("must_obtain", False),
        }

        if has_clearance or clearance.get("must_obtain"):
            matched.append(item)
        else:
            missing.append(item)

    # Check required skills
    for skill in requirements.get("skills_required", []):
        skill_lower = skill.lower()
        has_skill = skill_lower in resume_lower

        item = {"type": "skill_required", "description": skill}

        if has_skill:
            matched.append(item)
        else:
            missing.append(item)

    # Summary
    total = len(matched) + len(missing)
    match_pct = int((len(matched) / total) * 100) if total > 0 else 0

    return {
        "matched": matched,
        "missing": missing,
        "match_summary": {
            "total_requirements": total,
            "matched_count": len(matched),
            "missing_count": len(missing),
            "match_percentage": match_pct,
            "experience_match": len([m for m in matched if m["type"] == "experience"]),
            "skills_match": len([m for m in matched if m["type"] == "skill_required"]),
        },
    }


# Comprehensive list of tech skills to detect
TECH_SKILLS = {
    "languages": [
        "python",
        "javascript",
        "typescript",
        "java",
        "c++",
        "c#",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "r",
        "sql",
        "bash",
        "perl",
        "lua",
        "haskell",
        "elixir",
        "clojure",
        "dart",
        "objective-c",
    ],
    "frontend": [
        "react",
        "angular",
        "vue",
        "vue.js",
        "next.js",
        "nextjs",
        "nuxt",
        "svelte",
        "redux",
        "mobx",
        "tailwind",
        "tailwindcss",
        "css",
        "sass",
        "scss",
        "less",
        "html",
        "html5",
        "webpack",
        "vite",
        "babel",
        "jquery",
        "bootstrap",
        "material-ui",
        "mui",
        "chakra",
        "styled-components",
        "emotion",
    ],
    "backend": [
        "node",
        "node.js",
        "nodejs",
        "express",
        "express.js",
        "django",
        "flask",
        "fastapi",
        "spring",
        "spring boot",
        "rails",
        "ruby on rails",
        "laravel",
        ".net",
        "asp.net",
        "nest.js",
        "nestjs",
        "koa",
        "hapi",
        "gin",
        "echo",
        "fiber",
        "actix",
        "rocket",
    ],
    "cloud": [
        "aws",
        "amazon web services",
        "azure",
        "gcp",
        "google cloud",
        "cloud",
        "lambda",
        "ec2",
        "s3",
        "cloudfront",
        "api gateway",
        "cloudwatch",
        "ecs",
        "eks",
        "fargate",
        "cloudformation",
        "cdk",
    ],
    "devops": [
        "kubernetes",
        "k8s",
        "docker",
        "terraform",
        "ansible",
        "puppet",
        "chef",
        "jenkins",
        "ci/cd",
        "github actions",
        "gitlab ci",
        "circleci",
        "travis",
        "argocd",
        "helm",
        "prometheus",
        "grafana",
        "datadog",
        "splunk",
    ],
    "databases": [
        "postgresql",
        "postgres",
        "mysql",
        "mariadb",
        "mongodb",
        "redis",
        "elasticsearch",
        "dynamodb",
        "cassandra",
        "sqlite",
        "oracle",
        "sql server",
        "neo4j",
        "couchdb",
        "firebase",
        "supabase",
    ],
    "data": [
        "spark",
        "hadoop",
        "kafka",
        "airflow",
        "dbt",
        "snowflake",
        "redshift",
        "bigquery",
        "databricks",
        "pandas",
        "numpy",
        "etl",
        "data pipeline",
    ],
    "ai_ml": [
        "machine learning",
        "ml",
        "deep learning",
        "tensorflow",
        "pytorch",
        "keras",
        "scikit-learn",
        "sklearn",
        "nlp",
        "computer vision",
        "llm",
        "openai",
        "huggingface",
        "langchain",
        "rag",
    ],
    "tools": [
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "jira",
        "confluence",
        "slack",
        "figma",
        "postman",
        "swagger",
        "openapi",
        "vscode",
        "vim",
        "linux",
        "unix",
        "macos",
        "windows",
    ],
    "concepts": [
        "rest",
        "rest api",
        "graphql",
        "grpc",
        "microservices",
        "serverless",
        "event-driven",
        "message queue",
        "websocket",
        "oauth",
        "jwt",
        "testing",
        "tdd",
        "unit testing",
        "integration testing",
        "e2e",
        "agile",
        "scrum",
        "kanban",
    ],
}


def extract_all_skills_from_text(text: str) -> Dict[str, List[str]]:
    """Extract all tech skills found in text, categorized."""
    if not text:
        return {}

    text_lower = text.lower()
    found_skills = {}

    for category, skills in TECH_SKILLS.items():
        category_skills = []
        for skill in skills:
            # Check for skill presence (word boundary aware for short skills)
            if len(skill) <= 3:
                # Use word boundary for short skills like "go", "r", "sql"
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, text_lower):
                    category_skills.append(skill)
            else:
                if skill in text_lower:
                    category_skills.append(skill)

        if category_skills:
            found_skills[category] = category_skills

    return found_skills


def extract_required_skills(job_description: str) -> Dict[str, Any]:
    """
    Extract required and preferred skills from a job description.

    Returns:
        Dictionary with:
        - required: List of required skills
        - preferred: List of preferred/nice-to-have skills
        - all_skills: All skills mentioned categorized
    """
    if not job_description:
        return {"required": [], "preferred": [], "all_skills": {}}

    text_lower = job_description.lower()

    # Find all skills in the document
    all_skills = extract_all_skills_from_text(job_description)

    # Try to identify required vs preferred sections
    required_section = ""
    preferred_section = ""

    # Common section headers
    required_patterns = [
        r"(?:required|minimum|must have|essential)[\s\w]*(?:qualifications?|requirements?|skills?|experience)?:?\s*([\s\S]*?)(?=(?:preferred|nice to have|bonus|desired|plus|\n\n|$))",
        r"what you(?:'ll)? need:?\s*([\s\S]*?)(?=(?:what we|preferred|bonus|\n\n|$))",
        r"requirements?:?\s*([\s\S]*?)(?=(?:preferred|bonus|benefits|\n\n|$))",
    ]

    preferred_patterns = [
        r"(?:preferred|nice to have|bonus|desired|plus)[\s\w]*(?:qualifications?|requirements?|skills?)?:?\s*([\s\S]*?)(?=(?:benefits|about|equal opportunity|\n\n|$))",
    ]

    for pattern in required_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            required_section = match.group(1)
            break

    for pattern in preferred_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            preferred_section = match.group(1)
            break

    # Extract skills from each section
    required_skills_dict = (
        extract_all_skills_from_text(required_section) if required_section else {}
    )
    preferred_skills_dict = (
        extract_all_skills_from_text(preferred_section) if preferred_section else {}
    )

    # Flatten and dedupe
    required_skills = []
    for skills in required_skills_dict.values():
        required_skills.extend(skills)
    required_skills = list(set(required_skills))

    preferred_skills = []
    for skills in preferred_skills_dict.values():
        preferred_skills.extend(skills)
    preferred_skills = list(set(s for s in preferred_skills if s not in required_skills))

    # If we couldn't find sections, use all skills as required
    if not required_skills and not preferred_skills:
        for skills in all_skills.values():
            required_skills.extend(skills)
        required_skills = list(set(required_skills))

    return {
        "required": sorted(required_skills),
        "preferred": sorted(preferred_skills),
        "all_skills": all_skills,
    }


def create_tech_stack_overlap(job_description: str, resume_text: str) -> Dict[str, Any]:
    """
    Create a detailed tech stack overlap analysis.

    Returns:
        Dictionary with:
        - matched: Skills in both job and resume (categorized)
        - missing: Skills in job but not resume (categorized)
        - extra: Skills in resume but not in job (could be valuable)
        - match_percentage: Overall match percentage
        - summary: Quick summary stats
    """
    job_skills = extract_all_skills_from_text(job_description)
    resume_skills = extract_all_skills_from_text(resume_text)

    matched = {}
    missing = {}
    extra = {}

    all_categories = set(job_skills.keys()) | set(resume_skills.keys())

    total_job_skills = 0
    total_matched = 0

    for category in all_categories:
        job_cat_skills = set(job_skills.get(category, []))
        resume_cat_skills = set(resume_skills.get(category, []))

        cat_matched = job_cat_skills & resume_cat_skills
        cat_missing = job_cat_skills - resume_cat_skills
        cat_extra = resume_cat_skills - job_cat_skills

        if cat_matched:
            matched[category] = sorted(list(cat_matched))
            total_matched += len(cat_matched)
        if cat_missing:
            missing[category] = sorted(list(cat_missing))
        if cat_extra:
            extra[category] = sorted(list(cat_extra))

        total_job_skills += len(job_cat_skills)

    # Calculate match percentage
    if total_job_skills > 0:
        match_percentage = int((total_matched / total_job_skills) * 100)
    else:
        match_percentage = 0

    # Flatten for summary
    all_matched = []
    all_missing = []
    for skills in matched.values():
        all_matched.extend(skills)
    for skills in missing.values():
        all_missing.extend(skills)

    return {
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "match_percentage": match_percentage,
        "summary": {
            "matched_count": len(all_matched),
            "missing_count": len(all_missing),
            "top_matched": all_matched[:10],
            "critical_missing": all_missing[:5],
        },
    }


def extract_experience_requirements(job_description: str) -> List[Dict[str, Any]]:
    """
    Extract specific experience requirements from a job description.

    Looks for patterns like:
    - "3+ years of Python"
    - "5 years experience with AWS"
    - "2-4 years of React development"

    Args:
        job_description: The full job description text

    Returns:
        List of dictionaries with:
        - skill: The skill/technology
        - years_min: Minimum years required
        - years_max: Maximum years (if range specified)
        - raw_text: Original matched text
    """
    if not job_description:
        return []

    requirements = []
    text = job_description.lower()

    # Patterns to match experience requirements
    patterns = [
        # "3+ years of Python" or "3+ years Python"
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([a-zA-Z0-9\s\.\+\#\/\-]+?)(?:\s+experience|\s+development|\s+programming)?(?:[,\.]|\s+and|\s+or|$)",
        # "3-5 years of Python"
        r"(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([a-zA-Z0-9\s\.\+\#\/\-]+?)(?:\s+experience|\s+development)?(?:[,\.]|\s+and|\s+or|$)",
        # "experience with Python (3+ years)"
        r"(?:experience\s+(?:with|in)\s+)([a-zA-Z0-9\s\.\+\#\/\-]+?)\s*\((\d+)\+?\s*(?:years?|yrs?)\)",
        # "Python: 3+ years" or "Python - 3 years"
        r"([a-zA-Z0-9\s\.\+\#\/]+?)[\:\-]\s*(\d+)\+?\s*(?:years?|yrs?)",
        # "minimum 3 years of Python"
        r"(?:minimum|min|at\s+least)\s+(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([a-zA-Z0-9\s\.\+\#\/\-]+)",
    ]

    # Skills to look for (common tech skills)
    tech_skills = [
        "python",
        "javascript",
        "typescript",
        "java",
        "c++",
        "c#",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "r",
        "sql",
        "react",
        "angular",
        "vue",
        "node",
        "nodejs",
        "express",
        "django",
        "flask",
        "spring",
        "rails",
        "laravel",
        ".net",
        "dotnet",
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "cloud",
        "kubernetes",
        "k8s",
        "docker",
        "terraform",
        "ansible",
        "jenkins",
        "ci/cd",
        "devops",
        "linux",
        "unix",
        "windows server",
        "networking",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "kafka",
        "machine learning",
        "ml",
        "ai",
        "data science",
        "deep learning",
        "security",
        "cybersecurity",
        "devsecops",
        "penetration testing",
        "agile",
        "scrum",
        "project management",
        "leadership",
        "frontend",
        "backend",
        "full stack",
        "fullstack",
        "full-stack",
        "mobile",
        "ios",
        "android",
        "react native",
        "flutter",
        "api",
        "rest",
        "graphql",
        "microservices",
    ]

    seen_skills = set()

    # Try each pattern
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()

            # Parse based on pattern structure
            if len(groups) == 2:
                # Pattern with years first, then skill
                if groups[0].isdigit():
                    years_str, skill = groups
                    years_min = int(years_str)
                    years_max = None
                else:
                    # Pattern with skill first, then years
                    skill, years_str = groups
                    years_min = int(years_str)
                    years_max = None
            elif len(groups) == 3:
                # Range pattern: min-max years skill
                if groups[0].isdigit() and groups[1].isdigit():
                    years_min = int(groups[0])
                    years_max = int(groups[1])
                    skill = groups[2]
                else:
                    # skill (years) pattern
                    skill = groups[0]
                    years_min = int(groups[1])
                    years_max = None
            else:
                continue

            # Clean up skill name
            skill = skill.strip().strip(".,;:")

            # Skip if skill is too short or too long
            if len(skill) < 2 or len(skill) > 50:
                continue

            # Skip common non-skill words
            skip_words = [
                "experience",
                "required",
                "preferred",
                "minimum",
                "years",
                "the",
                "and",
                "or",
                "with",
                "in",
                "of",
                "for",
                "a",
                "an",
                "role",
                "position",
                "job",
                "work",
                "working",
                "related",
            ]
            if skill.lower() in skip_words:
                continue

            # Create unique key to avoid duplicates
            skill_key = skill.lower().strip()
            if skill_key in seen_skills:
                continue
            seen_skills.add(skill_key)

            requirements.append(
                {
                    "skill": skill.title() if len(skill) > 3 else skill.upper(),
                    "years_min": years_min,
                    "years_max": years_max,
                    "raw_text": match.group(0).strip()[:100],
                }
            )

    # Also look for general experience requirements
    general_patterns = [
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?(?:software|engineering|development)\s+experience",
            "Software Development",
        ),
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?(?:industry|work)\s+experience",
            "Professional Experience",
        ),
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant|related)\s+experience",
            "Relevant Experience",
        ),
    ]

    for pattern, skill_name in general_patterns:
        match = re.search(pattern, text)
        if match:
            skill_key = skill_name.lower()
            if skill_key not in seen_skills:
                seen_skills.add(skill_key)
                requirements.append(
                    {
                        "skill": skill_name,
                        "years_min": int(match.group(1)),
                        "years_max": None,
                        "raw_text": match.group(0).strip()[:100],
                    }
                )

    # Sort by years required (descending)
    requirements.sort(key=lambda x: x["years_min"], reverse=True)

    return requirements[:15]  # Limit to top 15


def analyze_job_fit(
    job_description: str,
    resume_text: str,
    job_title: str = "",
    experience_requirements: List[Dict] = None,
) -> Dict[str, Any]:
    """
    Analyze how well a candidate fits a job based on description and resume.

    Args:
        job_description: The job description text
        resume_text: The candidate's resume text
        job_title: The job title (for context)
        experience_requirements: Pre-extracted experience requirements

    Returns:
        Dictionary with:
        - pros: List of strengths/matches
        - gaps: List of gaps/missing requirements
        - match_score: Overall match percentage (0-100)
    """
    if not job_description or not resume_text:
        return {"pros": [], "gaps": [], "match_score": 0}

    job_lower = job_description.lower()
    resume_lower = resume_text.lower()

    pros = []
    gaps = []

    # Key skills to look for
    skill_categories = {
        "Languages": [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "c#",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "sql",
        ],
        "Frontend": [
            "react",
            "angular",
            "vue",
            "next.js",
            "nextjs",
            "redux",
            "tailwind",
            "css",
            "html",
            "webpack",
            "vite",
        ],
        "Backend": [
            "node",
            "express",
            "django",
            "flask",
            "spring",
            "fastapi",
            "rails",
            "laravel",
            ".net",
            "graphql",
            "rest api",
        ],
        "Cloud & DevOps": [
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "kubernetes",
            "docker",
            "terraform",
            "ansible",
            "jenkins",
            "ci/cd",
            "github actions",
        ],
        "Databases": [
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "dynamodb",
            "cassandra",
            "sqlite",
        ],
        "Other Skills": [
            "git",
            "linux",
            "agile",
            "scrum",
            "microservices",
            "api design",
            "testing",
            "security",
            "machine learning",
            "data science",
        ],
    }

    matched_skills = []
    missing_skills = []

    for category, skills in skill_categories.items():
        for skill in skills:
            in_job = skill in job_lower
            in_resume = skill in resume_lower

            if in_job and in_resume:
                matched_skills.append(skill.title() if len(skill) > 3 else skill.upper())
            elif in_job and not in_resume:
                missing_skills.append(skill.title() if len(skill) > 3 else skill.upper())

    # Build pros list
    if matched_skills:
        # Group by importance (first 5 are most relevant)
        top_matches = matched_skills[:5]
        if top_matches:
            pros.append(
                {
                    "type": "skills",
                    "title": "Strong Skill Match",
                    "description": f"Your resume shows experience with: {', '.join(top_matches)}",
                    "skills": top_matches,
                }
            )

        if len(matched_skills) > 5:
            other_matches = matched_skills[5:10]
            pros.append(
                {
                    "type": "skills",
                    "title": "Additional Matching Skills",
                    "description": f"Also matches: {', '.join(other_matches)}",
                    "skills": other_matches,
                }
            )

    # Check for experience level match
    experience_keywords = {
        "senior": ["senior", "sr.", "lead", "principal", "staff"],
        "mid": ["mid-level", "mid level", "intermediate"],
        "junior": ["junior", "jr.", "entry", "associate", "graduate"],
    }

    for level, keywords in experience_keywords.items():
        job_has_level = any(kw in job_lower for kw in keywords)
        resume_has_level = any(kw in resume_lower for kw in keywords)

        if job_has_level and resume_has_level:
            pros.append(
                {
                    "type": "experience",
                    "title": f"{level.title()} Level Match",
                    "description": f"Your experience level aligns with this {level} position",
                }
            )

    # Check for education match
    edu_keywords = ["bachelor", "master", "phd", "degree", "computer science", "engineering"]
    job_edu = [kw for kw in edu_keywords if kw in job_lower]
    resume_edu = [kw for kw in edu_keywords if kw in resume_lower]

    if job_edu and resume_edu:
        pros.append(
            {
                "type": "education",
                "title": "Education Match",
                "description": "Your educational background matches requirements",
            }
        )

    # Build gaps list
    if missing_skills:
        # Prioritize gaps based on frequency in job description
        skill_freq = {}
        for skill in missing_skills:
            skill_freq[skill] = job_lower.count(skill.lower())

        sorted_missing = sorted(missing_skills, key=lambda s: skill_freq.get(s, 0), reverse=True)

        critical_gaps = sorted_missing[:3]
        if critical_gaps:
            gaps.append(
                {
                    "type": "skills",
                    "title": "Key Skills to Highlight or Develop",
                    "description": f"Consider addressing: {', '.join(critical_gaps)}",
                    "skills": critical_gaps,
                    "severity": "medium",
                }
            )

        if len(sorted_missing) > 3:
            other_gaps = sorted_missing[3:7]
            gaps.append(
                {
                    "type": "skills",
                    "title": "Additional Skills Mentioned",
                    "description": f"Also listed: {', '.join(other_gaps)}",
                    "skills": other_gaps,
                    "severity": "low",
                }
            )

    # Check experience requirement gaps
    if experience_requirements:
        for req in experience_requirements[:5]:
            skill = req["skill"].lower()
            years_needed = req["years_min"]

            # Check if skill is in resume
            if skill not in resume_lower:
                gaps.append(
                    {
                        "type": "experience",
                        "title": f"{req['skill']} Experience",
                        "description": f"Requires {years_needed}+ years of {req['skill']}",
                        "years_required": years_needed,
                        "severity": "high" if years_needed >= 5 else "medium",
                    }
                )

    # Calculate match score
    total_job_skills = len(set(missing_skills + matched_skills))
    if total_job_skills > 0:
        match_score = int((len(matched_skills) / total_job_skills) * 100)
    else:
        match_score = 50  # Default if no skills detected

    # Adjust score based on experience match
    if any(p["type"] == "experience" for p in pros):
        match_score = min(100, match_score + 10)

    # Cap gaps list
    gaps = gaps[:5]
    pros = pros[:5]

    return {
        "pros": pros,
        "gaps": gaps,
        "match_score": match_score,
        "matched_skills_count": len(matched_skills),
        "missing_skills_count": len(missing_skills),
    }


def analyze_job_with_ai(
    job_description: str,
    resume_text: str,
    job_title: str,
    company: str,
) -> Dict[str, Any]:
    """
    Use AI to analyze job fit (more accurate but uses API credits).

    Args:
        job_description: The job description
        resume_text: The candidate's resume
        job_title: Job title
        company: Company name

    Returns:
        Analysis results from AI
    """
    try:
        from app.ai import get_provider

        provider = get_provider()

        prompt = f"""Analyze this job posting against the candidate's resume.

JOB: {job_title} at {company}

JOB DESCRIPTION:
{job_description[:3000]}

CANDIDATE RESUME:
{resume_text[:2000]}

Provide a JSON response with:
1. "experience_requirements": List of specific experience requirements found (skill, years_min, years_max)
2. "pros": List of 3-5 strengths where the candidate matches well (title, description)
3. "gaps": List of 2-4 potential gaps or areas to address (title, description, severity: high/medium/low)
4. "match_percentage": Overall match score 0-100

Respond ONLY with valid JSON, no other text."""

        response = provider.generate(prompt, max_tokens=1000)

        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI analysis response as JSON")

    except Exception as e:
        logger.error(f"AI job analysis failed: {e}")

    # Fall back to rule-based analysis
    return None


def detect_red_flags(
    job_description: str,
    job_title: str,
    company: str,
    posted_date: str = None,
    applicant_count: int = None,
) -> List[Dict[str, Any]]:
    """
    Detect red flags in a job posting that might indicate it's not worth applying.

    Returns list of red flags with:
    - flag: Short description
    - severity: "critical" | "warning" | "info"
    - reason: Detailed explanation
    """
    red_flags = []

    if not job_description:
        return red_flags

    text_lower = job_description.lower()
    title_lower = job_title.lower() if job_title else ""
    company_lower = company.lower() if company else ""

    # === STALE POSTING DETECTION ===
    if posted_date:
        try:
            from datetime import datetime, timedelta

            if isinstance(posted_date, str):
                # Parse relative dates like "1 month ago", "2 weeks ago"
                if "month" in posted_date.lower():
                    months = int(re.search(r"(\d+)", posted_date).group(1))
                    if months >= 1:
                        red_flags.append(
                            {
                                "flag": "Stale posting",
                                "severity": "warning",
                                "reason": f"Posted {months} month(s) ago - may be filled or have many applicants",
                            }
                        )
                elif "week" in posted_date.lower():
                    weeks = int(re.search(r"(\d+)", posted_date).group(1))
                    if weeks >= 3:
                        red_flags.append(
                            {
                                "flag": "Older posting",
                                "severity": "info",
                                "reason": f"Posted {weeks} weeks ago",
                            }
                        )
        except:
            pass

    # === HIGH APPLICANT COUNT ===
    if applicant_count and applicant_count > 100:
        red_flags.append(
            {
                "flag": "High competition",
                "severity": "warning",
                "reason": f"Over {applicant_count} applicants - very competitive",
            }
        )

    # === SCAM INDICATORS ===
    scam_patterns = [
        (r"no\s+experience\s+required", "Too good to be true - no experience for technical role"),
        (r"work\s+from\s+home\s+\$\d+k", "Suspicious work-from-home salary claim"),
        (r"unlimited\s+earning", "MLM/scam language"),
        (r"be\s+your\s+own\s+boss", "MLM/scam language"),
        (r"(?:urgent|immediate)\s+(?:hire|hiring|start)", "Pressure tactics"),
    ]

    for pattern, reason in scam_patterns:
        if re.search(pattern, text_lower):
            red_flags.append(
                {"flag": "Potential scam indicator", "severity": "critical", "reason": reason}
            )

    # Generic/vague company description
    if not company or company_lower in ["unknown", "confidential", "staffing agency"]:
        red_flags.append(
            {
                "flag": "Hidden company",
                "severity": "warning",
                "reason": "Company name not disclosed - could be recruiter farming or fake",
            }
        )

    # AI-generated content indicators
    ai_phrases = [
        "as a fully remote position",
        "you'll have the flexibility to work from any location",
        "our team uses tools like slack for daily chats",
        "we emphasize asynchronous work",
    ]
    ai_count = sum(1 for phrase in ai_phrases if phrase in text_lower)
    if ai_count >= 3:
        red_flags.append(
            {
                "flag": "Possibly AI-generated",
                "severity": "warning",
                "reason": "Job description appears template/AI-generated with generic details",
            }
        )

    # === CULTURE RED FLAGS ===
    culture_issues = [
        (r"not\s+a\s+9[\s-]to[\s-]5", "Expects overtime as standard", "warning"),
        (r"fast[\s-]paced\s+environment", "May indicate poor work-life balance", "info"),
        (r"wear\s+many\s+hats", "Underfunded - will do multiple jobs", "info"),
        (r"like\s+a\s+family", "Boundary issues, unpaid overtime expected", "warning"),
        (r"50[\s-]60\+?\s+hours?", "Explicitly requires 50-60+ hour weeks", "critical"),
        (r"60[\s-]80\+?\s+hours?", "Explicitly requires 60-80+ hour weeks", "critical"),
        (r"most\s+challenging\s+job", "Warning sign for unrealistic expectations", "warning"),
        (r"hustle", "Hustle culture, likely overwork expected", "warning"),
        (r"rockstar|ninja|guru", "Cringe culture, unrealistic role expectations", "info"),
    ]

    for pattern, reason, severity in culture_issues:
        if re.search(pattern, text_lower):
            red_flags.append({"flag": "Culture concern", "severity": severity, "reason": reason})

    # === COMPENSATION RED FLAGS ===
    # Low salary for senior role
    salary_match = re.search(r"\$(\d{2,3})[,\s]*(\d{3})?", job_description)
    if salary_match and "senior" in title_lower:
        try:
            salary = int(salary_match.group(1)) * 1000
            if salary_match.group(2):
                salary = int(salary_match.group(1) + salary_match.group(2))
            if salary < 100000:
                red_flags.append(
                    {
                        "flag": "Low salary for level",
                        "severity": "warning",
                        "reason": f"${salary:,} seems low for a senior role",
                    }
                )
        except:
            pass

    # No salary listed
    if not salary_match and not any(
        w in text_lower for w in ["competitive salary", "compensation", "pay range"]
    ):
        red_flags.append(
            {"flag": "No salary info", "severity": "info", "reason": "Salary not disclosed"}
        )

    return red_flags


def analyze_job_comprehensive(
    job_description: str,
    resume_text: str,
    job_title: str = "",
    company: str = "",
    posted_date: str = None,
    applicant_count: int = None,
    all_resumes: List[Dict] = None,
) -> Dict[str, Any]:
    """
    Comprehensive job analysis that mimics Claude's job review style.

    Returns:
    - recommendation: "apply" | "skip" | "maybe"
    - recommendation_reason: Clear explanation why
    - requirements: Extracted structured requirements
    - requirements_match: What you have vs what you're missing
    - red_flags: List of concerns
    - resume_recommendation: Which resume to use
    - experience_gaps: Specific experience year gaps
    - key_dealbreakers: Critical missing requirements
    """
    result = {
        "recommendation": "maybe",
        "recommendation_reason": "",
        "requirements": {},
        "requirements_match": {},
        "red_flags": [],
        "resume_recommendation": None,
        "experience_gaps": [],
        "key_dealbreakers": [],
        "strengths": [],
        "analysis_summary": "",
    }

    if not job_description:
        result["recommendation"] = "skip"
        result["recommendation_reason"] = "No job description available"
        return result

    # === 1. EXTRACT STRUCTURED REQUIREMENTS ===
    requirements = extract_structured_requirements(job_description)
    result["requirements"] = requirements

    # === 2. DETECT RED FLAGS ===
    red_flags = detect_red_flags(job_description, job_title, company, posted_date, applicant_count)
    result["red_flags"] = red_flags

    # Check for critical red flags
    critical_flags = [f for f in red_flags if f["severity"] == "critical"]
    if critical_flags:
        result["recommendation"] = "skip"
        result["recommendation_reason"] = critical_flags[0]["reason"]
        return result

    # === 3. MATCH REQUIREMENTS TO RESUME ===
    if resume_text:
        req_match = match_requirements_to_resume(requirements, resume_text)
        result["requirements_match"] = req_match

        # Identify key dealbreakers
        dealbreakers = []

        # Check experience gaps
        resume_lower = resume_text.lower()
        for exp in requirements.get("experience", []):
            skill = exp.get("skill", "").lower()
            years = exp.get("years", 0)

            # Check if this is a core skill not in resume
            skill_present = any(
                s in resume_lower for s in [skill, skill.replace(" ", ""), skill.replace("-", " ")]
            )

            if not skill_present and years >= 3:
                dealbreakers.append(
                    {
                        "type": "experience",
                        "requirement": f"{years}+ years of {exp.get('skill', 'experience')}",
                        "reason": f"Resume doesn't show {exp.get('skill')} experience",
                    }
                )
                result["experience_gaps"].append(
                    {"skill": exp.get("skill"), "years_required": years, "has_skill": False}
                )

        # Check clearance requirements
        clearance = requirements.get("clearance")
        if clearance and clearance.get("current_required"):
            clearance_terms = ["clearance", "secret", "ts/sci", "public trust", "top secret"]
            has_clearance = any(term in resume_lower for term in clearance_terms)
            if not has_clearance:
                dealbreakers.append(
                    {
                        "type": "clearance",
                        "requirement": f"{clearance.get('level')} clearance",
                        "reason": "Requires active clearance, not just eligibility",
                    }
                )

        # Check required certifications
        for cert in requirements.get("certifications", []):
            if cert.get("required"):
                cert_name = cert.get("name", "").lower()
                has_cert = cert_name in resume_lower or cert_name.replace(" ", "") in resume_lower
                if not has_cert:
                    dealbreakers.append(
                        {
                            "type": "certification",
                            "requirement": cert.get("name"),
                            "reason": f"Required certification not found in resume",
                        }
                    )

        result["key_dealbreakers"] = dealbreakers

        # Identify strengths
        strengths = []
        for item in req_match.get("matched", []):
            if item.get("type") == "experience":
                strengths.append(f"Has {item.get('description')}")
            elif item.get("type") == "skill_required":
                strengths.append(f"Knows {item.get('description')}")
            elif item.get("type") == "certification":
                strengths.append(f"Has {item.get('description')}")
        result["strengths"] = strengths[:10]

        # === 4. DETERMINE RECOMMENDATION ===
        match_pct = req_match.get("match_summary", {}).get("match_percentage", 0)

        # Critical dealbreakers = skip
        if len(dealbreakers) >= 3:
            result["recommendation"] = "skip"
            result["recommendation_reason"] = (
                f"Multiple dealbreakers: {', '.join([d['requirement'] for d in dealbreakers[:3]])}"
            )
        elif any(d["type"] == "clearance" for d in dealbreakers):
            result["recommendation"] = "skip"
            clearance_db = next(d for d in dealbreakers if d["type"] == "clearance")
            result["recommendation_reason"] = (
                f"Requires active {clearance_db['requirement']}, not just eligibility"
            )
        elif any(d["type"] == "certification" for d in dealbreakers):
            cert_dbs = [d for d in dealbreakers if d["type"] == "certification"]
            result["recommendation"] = "skip"
            result["recommendation_reason"] = (
                f"Required certification: {cert_dbs[0]['requirement']}"
            )
        elif match_pct >= 70:
            result["recommendation"] = "apply"
            result["recommendation_reason"] = f"{match_pct}% requirements match - good fit"
        elif match_pct >= 50:
            result["recommendation"] = "maybe"
            missing_count = req_match.get("match_summary", {}).get("missing_count", 0)
            result["recommendation_reason"] = f"{match_pct}% match, {missing_count} gaps to address"
        else:
            result["recommendation"] = "skip"
            result["recommendation_reason"] = (
                f"Only {match_pct}% requirements match - too many gaps"
            )

    # === 5. RESUME RECOMMENDATION ===
    if all_resumes and len(all_resumes) > 1:
        best_resume = None
        best_match = 0

        for resume in all_resumes:
            resume_content = resume.get("content", "") or resume.get("full_text", "")
            if not resume_content:
                continue

            resume_match = match_requirements_to_resume(requirements, resume_content)
            match_pct = resume_match.get("match_summary", {}).get("match_percentage", 0)

            if match_pct > best_match:
                best_match = match_pct
                best_resume = {
                    "resume_id": resume.get("resume_id") or resume.get("id"),
                    "name": resume.get("name") or resume.get("title", "Resume"),
                    "match_percentage": match_pct,
                }

        if best_resume:
            result["resume_recommendation"] = best_resume

    # === 6. BUILD ANALYSIS SUMMARY ===
    summary_parts = []

    if result["recommendation"] == "skip":
        summary_parts.append(f"Skip. {result['recommendation_reason']}")
    elif result["recommendation"] == "apply":
        summary_parts.append(f"Apply! {result['recommendation_reason']}")
    else:
        summary_parts.append(f"Maybe. {result['recommendation_reason']}")

    # Add key gaps
    if result["experience_gaps"]:
        gaps = result["experience_gaps"][:3]
        gap_strs = [f"{g['years_required']}+ yrs {g['skill']}" for g in gaps]
        summary_parts.append(f"Missing: {', '.join(gap_strs)}")

    # Add red flags
    warning_flags = [f for f in red_flags if f["severity"] == "warning"]
    if warning_flags:
        summary_parts.append(f"Concerns: {warning_flags[0]['reason']}")

    result["analysis_summary"] = " | ".join(summary_parts)

    return result


def quick_pre_filter(job: Dict) -> Optional[Tuple[bool, int, str]]:
    """
    Quick rule-based pre-filtering to avoid expensive AI calls for obvious mismatches.

    Returns None if job should go to AI scoring, or (should_skip, score, reason) tuple.
    """
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    description = (job.get("job_description") or job.get("full_description") or "").lower()

    # Skip jobs with malformed/garbled titles
    if title:
        # Check for weird word order patterns like "Senior at Cloud Engineer"
        if " at " in title and not title.endswith(" at"):
            parts = title.split(" at ")
            if len(parts) == 2 and len(parts[0].split()) <= 2 and len(parts[1].split()) >= 2:
                return (True, 20, "Malformed job title")

        # Skip if title is too short or just numbers
        if len(title) < 5 or title.replace(" ", "").isdigit():
            return (True, 15, "Invalid job title")

    # Skip unknown companies
    if company in ["unknown", "confidential", "", "n/a"]:
        return (True, 25, "Unknown company")

    # Check for obvious role mismatches in title
    skip_titles = [
        "manager",
        "director",
        "vp ",
        "vice president",
        "chief ",
        "cto",
        "ceo",
        "cfo",
        "principal",
        "staff engineer",
        "distinguished",
        "fellow",
        "intern",
        "internship",
        "sales",
        "marketing",
        "recruiter",
        "hr ",
        "human resources",
        "nurse",
        "doctor",
        "physician",
        "lawyer",
        "attorney",
        "driver",
        "warehouse",
        "retail",
        "cashier",
    ]

    for skip in skip_titles:
        if skip in title:
            # These might still be valid, just lower priority
            return None

    # No pre-filter, let AI score it
    return None
