from dataclasses import dataclass, field


@dataclass
class Experience:
    title: str = ""
    company: str = ""
    start: str = ""
    end: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class Education:
    degree: str = ""
    institution: str = ""
    year: str = ""


@dataclass
class ResumeData:
    name: str = ""
    email: str = ""
    phone: str = ""
    links: list[str] = field(default_factory=list)
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experiences: list[Experience] = field(default_factory=list)
    educations: list[Education] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)


@dataclass
class JobSpec:
    raw: str = ""
    target_keywords: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class ScoreReport:
    parse_score: int = 0
    match_score: int = 0
    missing_keywords: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    def combined(self, parse_weight: float, match_weight: float) -> int:
        return round(parse_weight * self.parse_score + match_weight * self.match_score)
