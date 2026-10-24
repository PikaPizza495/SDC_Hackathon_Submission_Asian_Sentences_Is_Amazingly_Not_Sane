# InstaQuote

Our project targets SMEs to connect them with suppliers much more easily with a automated system.

## Team Information

| Field                  | Details                                     |
| ---------------------- | ------------------------------------------- |
| **Team Name**          | Asian Sentences Is Amazingly Not Sane       |
| **Team Domain**        | Domain 2                                    |
| **SDG Track (1–17)**   | SDG 8 Decent Work And Economic Growth       |
| **Team Leader**        | Teng Min Jie                                |
| **University**         | Asia Pacific University                     |
| **Number of Members**  | 5                                           |


## Links

| Resource          | Link                                           |
| ----------------- | ---------------------------------------------- |
| GitHub Repository | https://github.com/PikaPizza495/SDC_Hackathon_Submission_Asian_Sentences_Is_Amazingly_Not_Sane/tree/main  |
| Live Demo         | https://replit.com/join#t=ndujmumuxivpsyq-tengminjie878               |
| Slide Deck        | https://canva.link/8gxqyjicrhvuhhj                    |
| Demo Video        | To Be Added               |


## Overview

### Problem

Most owners or employee from SMEs have a hard time looking for suppliers that meet their requirements. Some SMEs also lack enough experience to make the best decision leading to consequences like overpaying, delayed stock, and missed opportunities from better suppliers. This matters because these consequences can lead the enterprises to fail and be bankrupted very easily.

### Solution

Our project, InstaQuote uses AI to help SMEs much more easily find suitable suppliers based many things like location, budget, availability, type of supply needed. This approach also allows the user to make the final call based on their preference.

### Key Features

- **Staff / Owner Role Switcher** – Simulate Staff (Requester) and SME Owner (Approver) with different permissions.
- **Business Needs / Procurement Request Form** – Staff can enter the product or service needed, quantity, maximum budget (RM), and preferred location.
- **Supplier & Business Directory** – Store synthetic supplier and business data, including company names, industries, products/services, prices, MOQ, delivery times, reliability ratings, locations, and contact details.
- **Smart Supplier & Business Discovery** – Help SMEs discover suitable suppliers and business contacts based on their specific needs, even if they do not know whom to approach.
- **Intelligent Matching & Filtering** – Automatically match and filter suppliers based on product/service compatibility, budget, MOQ, location, and delivery availability.
- **Top 3 Business Recommendations** – Recommend the three most suitable suppliers based on pricing, delivery speed, reliability, and business compatibility.
- **Business Profiles** – Display supplier information, products/services, locations, contact channels, and other relevant details to help SMEs evaluate potential business connections.
- **Explainable Recommendations** – Show why each supplier is recommended or rejected, helping SMEs make informed decisions.
- **AI Connection / RFQ Generator** – Generate editable, personalized business introduction messages or quotation requests (RFQs) in English or Bahasa Melayu.
- **Owner Approval Workflow** – Only the SME Owner can approve or reject an outreach request before contacting a supplier.
- **WhatsApp Connection / RFQ Link** – Generate a prefilled WhatsApp message after approval, allowing the Owner to manually contact the selected supplier without requiring WhatsApp API integration.
- **Audit / Activity Log** – Record procurement requests, selected suppliers, approval decisions, timestamps, and outreach statuses.


---

## Project Structure

```
.
├── docs/                    # Screenshots, diagrams
├── runpod/
│   └── handler.py           # RunPod serverless handler (GPU workload)
├── src/
│   ├── main.py              # Application entry point
│   └── utils.py             # Helper functions
├── submission/              # Required submission documents
│   ├── SDC2026_TeamName_Preliminary.pdf      # Preliminary submission
│   ├── SDC2026_TeamName_TechDeclaration.pdf  # Technology declaration
│   ├── SDC2026_TeamName_Replit_POU.pdf       # Replit proof of use
│   └── SDC2026_TeamName_Runpod_POU.pdf       # RunPod proof of use
├── tests/
│   └── test_utils.py        # Unit tests
├── .env.example             # Example environment variables
├── .gitignore
├── .replit                  # Replit run configuration
├── LICENSE
├── requirements.txt         # Python dependencies
└── README.md
```

> to be changed

### Architecture

```
User ──► Replit (App / API) ──► Response returned to user
                
```

---

## How To Run

### Run on Replit

1. Open https://replit.com/join#t=ndujmumuxivpsyq-tengminjie878 shown in the links section. (Will redirect you to our replit page)

(Note: The suppliers provided can be found in ['SRC/suppliers.csv'](SRC/suppliers.csv)

---

## How We Used Replit

- **Development**: Replit is used for Database and Website Development

Proof of Use: [`Submission/SDC2026_Asian_Sentences_Is_Amazingly_Not_Sane_Replit_POU.pdf`](Submission/SDC2026_Asian_Sentences_Is_Amazingly_Not_Sane_Replit_POU.pdf)

## Runpod Was Not Used For This Project

---

## Challenges and Learnings

- Poor Time Management. We overcame this by creating a clear and concrete goal and delegated task to everyone to make up for lost time
- We learned more on how to use Replit and Github

## Future Improvements

- Real WhatsApp Business API integration
- Automated supplier response and connection tracking
- AI quotation comparison and negotiation assistance
- Purchase order generation
- Inventory demand forecasting
- Verified supplier and business onboarding
- Smart business networking and partner recommendations
- Mutual business connections and referrals
- Supplier performance analytics and relationship management
- Live Orbyte ecosystem integration

## Team

| **Name**      | **Roles**    | **Github**                      |
| ---           | ---          | ---                             |
| Teng Min Jie  | Team Lead    | https://github.com/TENGMJ87845  |
| Lee Jun Yi    | Team Member  | https://github.com/LeeJY14      | 
| Tenka         | Team Member  | https://github.com/Tenka1412    |
| Xiang         | Team Member  | https://github.com/xiang878787  |
| Wong Pei Zhan | Team Member  | https://github.com/PikaPizza495 |

## Submission Checklist

- [✓] Team name, domain (Domain 1 / Domain 2) and SDG track filled in
- [✓] Slide deck link added
- [ ] Demo video link added
- [✓] Replit used, with proof of use in `submission/`
- [ ] Preliminary submission completed (`SDC2026_TeamName_Preliminary.pdf`)
- [ ] Technology declaration completed (`SDC2026_TeamName_TechDeclaration.pdf`)
- [ ] Submission files renamed with your team name (replace `TeamName`)
- [✓] "How to Run" steps verified
- [ ] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE).
