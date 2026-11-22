"""Hand-encoded data from the CS Undergraduate Handbook (rev. 6/25/2025), provided by the team.

Everything here was transcribed from the handbook; page references are in comments.
prereq is CNF: list of OR-groups that must ALL be satisfied.  status:
  stated      the source states the prerequisite (including "None")
  none_listed the source describes the course but lists no prerequisite
"""

SOURCE = "CS Undergraduate Handbook (rev. 6/25/2025)"

# code: (title, credits, prereq, coreq, note, status)        -- course descriptions, handbook pp. 20-26
CS_COURSES = {
    "GEEN 111": ("College of Engineering Colloquium", 1, [], [], "Freshman standing", "stated"),
    "COMP 120": ("Computers and Their Use", 3, [], [], "Not for credit by CS majors", "stated"),
    "COMP 121": ("Computer Science Freshmen Colloquium", 1, [], [], None, "stated"),
    "COMP 160": ("C++ Programming for Engineers", 3, [], [], None, "none_listed"),
    "COMP 161": ("Python for Data Science", 3, [], [], None, "stated"),
    "COMP 163": ("Introduction to Computer Programming", 3, [], [], None, "stated"),
    "COMP 167": ("Computer Program Design", 3, [["COMP 163"]], [], None, "stated"),
    "COMP 170": ("Introduction to Web Engineering", 4, [], [], None, "stated"),
    "COMP 180": ("Discrete Structures", 3, [["MATH 110", "MATH 131"]], [], None, "stated"),
    "COMP 200": ("Computer Science Sophomore Colloquium", 1, [], [], "Sophomore standing", "stated"),
    "COMP 267": ("Database Design", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 280": ("Data Structures", 3, [["COMP 167"], ["MATH 123", "COMP 180", "ECEN 227"]], [], None, "stated"),
    "COMP 285": ("Design and Analysis of Algorithms", 3, [["COMP 280"], ["MATH 131"]], [], None, "stated"),
    "COMP 300": ("Computer Science Junior Colloquium", 1, [], [], "Junior standing", "stated"),
    "COMP 320": ("Fundamentals of Cybersecurity", 3, [], [], "Elective table (p.19) says Junior standing; course description says None", "stated"),
    "COMP 321": ("Computer System Security", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 322": ("Internet Systems", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 323": ("Introduction to Health Care Information Systems", 3, [], [], "Junior standing", "stated"),
    "COMP 340": ("Game Intelligence", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 350": ("Operating Systems", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 356": ("Computational Hip-Hop and Object-Oriented Design", 3, [["COMP 163"]], [], "or instructor's permission", "stated"),
    "COMP 360": ("Programming Languages", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 361": ("Data Analytics in Python", 3, [["COMP 280"], ["MATH 351"], ["MATH 224", "ISEN 370", "ECEN 356"]], [], "'Statistics Electives' interpreted as the handbook's approved statistics list", "stated"),
    "COMP 363": ("Object Oriented Programming", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 365": ("Artificial Intelligence & Machine Learning", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 368": ("Object-Oriented Software Development", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 375": ("Computer Architecture and Organization", 3, [["COMP 280", "ECEN 327"]], [], None, "stated"),
    "COMP 385": ("Theory of Computing", 3, [["COMP 360"]], [], None, "stated"),
    "COMP 390": ("Social Implications of Computing", 3, [], [], None, "none_listed"),
    "COMP 397": ("Co-operative Industrial Experience I", 3, [], [], "Permission of advisor", "stated"),
    "COMP 410": ("Software Engineering", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 411": ("Introduction to System Testing and Evaluation", 3, [["COMP 410"]], [], None, "stated"),
    "COMP 420": ("Applied Network Security", 3, [["COMP 280"]], [], "or instructor's permission (elective table)", "stated"),
    "COMP 421": ("Security Management for Information Systems", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 422": ("Information Privacy and Security", 3, [["COMP 280"]], [], "or instructor's permission (elective table)", "stated"),
    "COMP 423": ("Web Security", 3, [["COMP 280"]], [], "or instructor's permission (elective table)", "stated"),
    "COMP 440": ("Game Design", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 452": ("Network Science", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 453": ("Introduction to Computer Graphics", 3, [["COMP 285"]], [], None, "stated"),
    "COMP 454": ("Virtual and Augmented Reality", 3, [["COMP 280"]], [], None, "stated"),
    "COMP 463": ("Introduction to Compiler Design", 3, [["COMP 285"], ["COMP 375"]], [], None, "stated"),
    "COMP 468": ("Introduction to Data Mining", 3, [["COMP 280"]], [], "or instructor's permission (elective table)", "stated"),
    "COMP 469": ("Introduction to Parallel Programming", 3, [["COMP 350"]], [], "or consent of instructor", "stated"),
    "COMP 476": ("Networked Computer Systems", 3, [["COMP 280", "ECEN 327"]], [], None, "stated"),
    "COMP 485": ("Special Topics in Computer Science", 3, [], [], "Instructor's permission (elective table)", "none_listed"),
    "COMP 494": ("Independent Study", 3, [], [], "Permission of instructor", "stated"),
    "COMP 495": ("Senior Project I", 3, [["COMP 285"]], ["COMP 410"], None, "stated"),
    "COMP 496": ("Senior Project II", 3, [["COMP 410"], ["COMP 495"]], [], None, "stated"),
}

# Courses named in the handbook without a description there: (title, credits, credits_inferred)
CS_OTHER = {
    "ENGL 331": ("Writing Science & Technology", 3, False),
    "MATH 110": ("Pre-Calculus", 3, True),
    "MATH 123": (None, 3, True),
    "MATH 224": ("Probability & Statistics", 3, True),
    "MATH 340": ("Numerical Methods", 3, True),
    "MATH 351": ("Linear Algebra and Matrix Theory", 3, False),
    "MATH 365": (None, 3, True),
    "ECEN 227": (None, 3, True),
    "ECEN 327": (None, 3, True),
    "ECEN 356": ("Probability and Random Variables", 3, False),
    "ECEN 375": ("Computer Architecture and Organization", 3, True),
    "ECEN 427": (None, 3, True),
    "ISEN 370": ("Engineering Statistics", 3, False),
    "ISEN 415": ("Discrete Event Systems Modeling and Simulation", 3, False),
    "BUAN 132": ("Introduction to Management Information Systems", 3, True),
    "BUAN 335": (None, 3, True),
    "CST 340": (None, 3, True),
    "MGMT 110": ("Business Environment", 3, True),
    "MKTG 230": ("Marketing", 3, True),
    "ECON 200": ("Principles of Economics (Micro)", 3, True),
    "ECON 201": ("Principles of Economics (Macro)", 3, True),
    "BIOL 100": ("Biological Science", 4, False),
    "BIOL 101": ("Concepts of Biology", 4, False),
    "SLMG 200": ("Soil Science", 4, False),
    "CHEM 107": ("General Chemistry VII", 3, True),
    "CHEM 117": ("General Chemistry VII Laboratory", 1, True),
}

# Minimum-grade policy (handbook p.5)
CS_MIN_GRADE = {"C": ["COMP 163", "COMP 167", "COMP 280", "COMP 285"], "C-": ["MATH 131"]}

# Footnote lists [1]-[7] and Gen Ed lists (handbook pp.6, 15-17)
CS_LISTS = {
    "CS_BUSINESS": ("Business elective (pick 1)", ["MGMT 110", "BUAN 132", "MKTG 230", "ECON 200", "ECON 201"]),
    "CS_MATH": ("Approved mathematics elective", ["MATH 340", "MATH 351"]),
    "CS_STATS": ("Approved statistics elective", ["MATH 224", "ISEN 370", "ECEN 356"]),
    "CS_ARCH": ("Approved computer architecture elective", ["COMP 375", "ECEN 375"]),
    "CS_SCIENCE": ("Approved science elective pool (12 hr from Group 1 or Group 2; group rule not enforced)",
                   ["CHEM 106", "CHEM 116", "CHEM 107", "CHEM 117", "PHYS 241", "PHYS 251", "PHYS 242",
                    "PHYS 252", "BIOL 100", "BIOL 101", "SLMG 200"]),
    # footnote [7]: approved CS electives (taken from the handbook's elective-prerequisite table, p.19) + listed externals
    "CS_COMP_ELECTIVES": ("Approved COMP electives (9 hr)",
                          ["COMP 320", "COMP 321", "COMP 323", "COMP 340", "COMP 356", "COMP 361", "COMP 363",
                           "COMP 368", "COMP 420", "COMP 421", "COMP 422", "COMP 423", "COMP 440", "COMP 454",
                           "COMP 469", "COMP 494", "COMP 411", "COMP 452", "COMP 453", "COMP 463", "COMP 468",
                           "COMP 485", "BUAN 335", "ECEN 427", "ISEN 415", "MATH 365", "CST 340"]),
}

GENED = {   # handbook p.17.  title, list
    "GENED_HUM": ("Humanities and Fine Arts electives",
                  ["ENGL 200", "ENGL 201", "ENGL 230", "ENGL 231", "ENGL 211", "ENGL 212", "LIBS 202", "MUSI 216",
                   "MUSI 220", "PHIL 101", "PHIL 103", "PHIL 104", "PHIL 201", "PHIL 266", "PHIL 267", "SPCH 250"]),
    "GENED_SOC": ("Social and Behavioral Sciences electives",
                  ["FIN 279", "ECON 200", "ECON 201", "FCS 135", "FCS 181", "FCS 260", "HIST 103", "HIST 104",
                   "HIST 105", "HIST 106", "HIST 107", "HIST 130", "HIST 206", "HIST 207", "HIST 216", "HIST 231",
                   "JOMC 240", "POLI 110", "PSYC 101", "SOCI 100", "SOCI 200", "SSFM 226"]),
    "GENED_AFAM": ("Knowledge of African American Culture and History",
                   ["ENGL 211", "ENGL 212", "HIST 103", "HIST 106", "HIST 107", "LIBS 202", "MUSI 220"]),
    "GENED_GLOBAL": ("Global Awareness",
                     ["HIST 130", "HIST 206", "HIST 207", "HIST 216", "HIST 231", "MGMT 221", "PHIL 103", "PHIL 201"]),
}

# Computer Science B.S. (starting Fall 2023), handbook p.6.  (term, kind, payload)
#   course: code ; elective: (label, category, credits, fill, list_ref)
CS_PLAN = [
    (1, "course", "ENGL 100"),
    (1, "elective", ("Social/Behavioral Sciences Elective", "social_behavioral", 3, "list", "GENED_SOC")),
    (1, "course", "COMP 163"), (1, "course", "GEEN 111"), (1, "course", "MATH 131"), (1, "course", "COMP 121"),
    (2, "course", "ENGL 101"),
    (2, "elective", ("Knowledge of African-American Culture and History", "african_american", 3, "list", "GENED_AFAM")),
    (2, "course", "COMP 167"), (2, "course", "COMP 180"), (2, "course", "MATH 132"),
    (3, "course", "SPCH 250"),
    (3, "elective", ("Approved Science Elective", "cs_science", 4, "list", "CS_SCIENCE")),
    (3, "elective", ("Business Elective", "business", 3, "list", "CS_BUSINESS")),
    (3, "course", "MATH 341"), (3, "course", "COMP 280"),
    (4, "elective", ("Global Awareness", "global_awareness", 3, "list", "GENED_GLOBAL")),
    (4, "elective", ("Approved Science Elective", "cs_science", 4, "list", "CS_SCIENCE")),
    (4, "course", "COMP 285"),
    (4, "elective", ("Approved Mathematics Elective", "cs_math", 3, "list", "CS_MATH")),
    (4, "course", "COMP 267"), (4, "course", "COMP 200"),
    (5, "elective", ("Approved Science Elective", "cs_science", 4, "list", "CS_SCIENCE")),
    (5, "elective", ("Approved Statistics Elective", "cs_stats", 3, "list", "CS_STATS")),
    (5, "course", "COMP 360"),
    (5, "elective", ("Approved Computer Architecture Elective", "cs_arch", 3, "list", "CS_ARCH")),
    (5, "elective", ("Approved COMP Elective", "cs_comp_elective", 3, "list", "CS_COMP_ELECTIVES")),
    (6, "course", "ENGL 331"), (6, "course", "COMP 322"), (6, "course", "COMP 365"),
    (6, "course", "COMP 350"), (6, "course", "COMP 410"), (6, "course", "COMP 300"),
    (7, "course", "COMP 385"), (7, "course", "COMP 390"), (7, "course", "COMP 476"), (7, "course", "COMP 495"),
    (8, "course", "COMP 496"),
    (8, "elective", ("Approved COMP Elective", "cs_comp_elective", 3, "list", "CS_COMP_ELECTIVES")),
    (8, "elective", ("Approved COMP Elective", "cs_comp_elective", 3, "list", "CS_COMP_ELECTIVES")),
    (8, "elective", ("Free Elective", "free", 3, "any", None)),
]
CS_SEM_TOTALS = {1: 15, 2: 16, 3: 16, 4: 17, 5: 16, 6: 16, 7: 12, 8: 12}   # as printed in the handbook

# NC community-college transfer curriculum for CS (handbook p.12, dated June 15, 2016).
# Codes are NC Community College System (NCCCS) Common Course Library codes -> valid at every NC community college.
# (cc_course, cc_title, credits, status, ncat_equiv|category, also_requires, note)
CS_TRANSFER = [
    ("ENG 111", None, 3, "direct", ["ENGL 100"], [], None),
    ("ENG 112", None, 3, "direct", ["ENGL 101"], [], None),
    ("MAT 271", None, 4, "direct", ["MATH 131"], [], None),
    ("MAT 272", None, 4, "direct", ["MATH 132"], [], None),
    ("MAT 167", None, 3, "direct", ["COMP 180"], [], None),
    ("CSC 151", None, 3, "direct", ["COMP 163"], [], None),
    ("CSC 251", None, 3, "direct", ["COMP 167"], [], None),
    ("COM 110", None, 3, "direct", ["SPCH 250"], [], None),
    ("MAT 285", None, 3, "direct", ["MATH 341"], [], None),
    ("CSC 249", None, 3, "direct", ["COMP 280"], [], None),
    ("DBA 115", None, 3, "direct", ["COMP 267"], [], None),
    ("CTI 120", None, 3, "direct", ["COMP 476"], [], "alternative to NET 110 + NET 125"),
    ("NET 110", None, 3, "direct", ["COMP 476"], ["NET 125"], "must be taken with NET 125"),
    ("NET 125", None, 3, "direct", ["COMP 476"], ["NET 110"], "must be taken with NET 110"),
    ("CTS 210", None, 3, "direct", ["COMP 390"], [], "alternative to HUM 110"),
    ("HUM 110", None, 3, "direct", ["COMP 390"], [], "alternative to CTS 210"),
    ("BUS 110", None, 3, "category", "business", [], "handbook lists as Business Elective"),
    ("MAT 280", None, 3, "category", "cs_math", [], "handbook lists as Approved Math Elective"),
    ("MAT 152", None, 3, "category", "cs_stats", [], "handbook lists as Approved Statistics Elective"),
    ("CHM 151", None, 4, "category", "cs_science", [], "credits inferred (12 hr = 3 courses); science group rule in note [1]"),
    ("CHM 152", None, 4, "category", "cs_science", [], "credits inferred"),
    ("PHY 251", None, 4, "category", "cs_science", [], "credits inferred"),
    ("PHY 252", None, 4, "category", "cs_science", [], "credits inferred"),
    ("BIO 110", None, 4, "category", "cs_science", [], "credits inferred"),
    ("BIO 111", None, 4, "category", "cs_science", [], "credits inferred"),
    ("NOS 244", None, 3, "category", "cs_comp_elective", [], "cybersecurity COMP elective (note [2])"),
    ("SEC 110", None, 3, "category", "cs_comp_elective", [], "cybersecurity COMP elective (note [2])"),
    ("SEC 150", None, 3, "category", "cs_comp_elective", [], "cybersecurity COMP elective (note [2])"),
    ("SEC 160", None, 3, "category", "cs_comp_elective", [], "cybersecurity COMP elective (note [2])"),
]
