// Three built-in demo resumes so every feature on the site can be tried instantly after
// deployment, without a real file upload. Loading one populates ResumeContext exactly like a
// real upload would - every downstream feature call (match, boost, cover letter, skills-gap,
// interview prep, chat, personalized analytics) still hits the real backend on real data.
// Chosen deliberately so between the three they exercise: strong/medium match scores, resume
// lines worth boosting, and missing skills both with and without a curated study link.

export const DEMO_RESUMES = [
  {
    id: "demo-junior-analyst",
    label: "Junior Data Analyst",
    persona: "Junior Data Analyst",
    text: `Priya Sharma
Junior Data Analyst

Summary
Data analyst with 1 year of experience turning raw datasets into decisions. Comfortable
across the full analysis workflow from cleaning to visualization to presenting findings.

Experience
Data Analyst Intern, Northwind Analytics (2024-2025)
- Was involved in cleaning and merging survey datasets using Python and Pandas.
- Helped with building dashboards in Excel for the marketing team.
- Wrote SQL queries to pull weekly reports from the PostgreSQL warehouse.
- Assisted in preparing a churn analysis that was presented to leadership.

Education
B.Sc. Statistics, Delhi University (2024)

Skills
Python, Pandas, NumPy, SQL, PostgreSQL, Excel, Statistics, Data Analysis, Data Wrangling`,
    skills: ["Python", "Pandas", "NumPy", "SQL", "PostgreSQL", "Excel", "Statistics", "Data Analysis", "Data Wrangling"],
    experience_years: 1,
  },
  {
    id: "demo-backend-engineer",
    label: "Backend Engineer",
    persona: "Mid-level Backend Engineer",
    text: `Arjun Mehta
Backend Software Engineer

Summary
Backend engineer with 4 years building and scaling REST APIs and services for
consumer-facing products. Comfortable owning a service end to end, from design to
production monitoring.

Experience
Software Engineer II, Fintrack Systems (2021-2025)
- Led the redesign of the payments service, cutting p99 latency by 40%.
- Built and maintained REST APIs in Node.js and Express.js serving 2M+ daily requests.
- Helped with migrating the primary datastore from MySQL to PostgreSQL.
- Was responsible for on-call rotation and incident response for the payments team.
- Containerized services with Docker and deployed via Kubernetes on AWS.

Software Engineer, Fintrack Systems (2020-2021)
- Worked on internal tooling for the data engineering team using Python and FastAPI.

Education
B.Tech Computer Science, VIT (2020)

Skills
Node.js, Express.js, Python, FastAPI, PostgreSQL, MySQL, Docker, Kubernetes, AWS,
REST APIs, Git, CI/CD`,
    skills: [
      "Node.js",
      "Express.js",
      "Python",
      "FastAPI",
      "PostgreSQL",
      "MySQL",
      "Docker",
      "Kubernetes",
      "AWS",
      "REST APIs",
      "Git",
      "CI/CD",
    ],
    experience_years: 4,
  },
  {
    id: "demo-product-manager",
    label: "Senior Product Manager",
    persona: "Senior Product Manager",
    text: `Sana Iyer
Senior Product Manager

Summary
Product manager with 7 years leading cross-functional teams from discovery to launch
across B2B SaaS products. Data-informed, comfortable partnering directly with engineering
and design.

Experience
Senior Product Manager, Cloudline (2022-2025)
- Was involved in defining the roadmap for the analytics product line, growing adoption 3x.
- Helped with running quarterly planning across 4 engineering pods.
- Partnered with design and engineering to ship a self-serve onboarding flow.
- Used SQL and Tableau to build reporting for weekly business reviews.

Product Manager, Cloudline (2019-2022)
- Owned the notifications platform end to end, from spec to launch.
- Ran user interviews and translated findings into a prioritized backlog using Jira.

Education
MBA, Indian Institute of Management (2019)
B.E. Information Technology, Mumbai University (2016)

Skills
Product Management, SQL, Tableau, Jira, Agile, Scrum, Communication, Leadership,
Data Analysis, Excel`,
    skills: [
      "Product Management",
      "SQL",
      "Tableau",
      "Jira",
      "Agile",
      "Scrum",
      "Communication",
      "Leadership",
      "Data Analysis",
      "Excel",
    ],
    experience_years: 7,
  },
];
