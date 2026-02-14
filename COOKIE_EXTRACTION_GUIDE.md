# 🍪 Cookie Extraction for Semi-Automated Web Scraping

## Overview

This document explains how `extract_cookies.py` works in a semi-automated web scraping workflow.

---

## 1. Overall Workflow

```mermaid
flowchart TD
    A[User Manually Logs In] --> B[Run extract_cookies.py]
    B --> C[Playwright Connects to Browser]
    C --> D[Extract Cookies]
    D --> E[Save to cookies.json]
    E --> F[Scrapy Spider Uses Cookies]
    
    subgraph Browser
    A
    end
    
    subgraph Python Script
    B
    C
    D
    E
    end
    
    subgraph Scrapy
    F
    end
```

---

## 2. Two Connection Modes

### Mode 1: Connect to Existing Browser

```mermaid
flowchart LR
    subgraph User_Chrome["Your Chrome Browser"]
        PC[Page with Cookies]
    end
    
    subgraph Connection["CDP Connection :9222"]
        CDPC[Chrome DevTools Protocol]
    end
    
    subgraph Script["extract_cookies.py"]
        CONNECT["connect_over_cdp"]
        EXTRACT["Extract cookies"]
    end
    
    PC -->|Has Session Cookie| CDPC
    CDPC -->|Connect| CONNECT
    CONNECT --> EXTRACT
```

### Mode 2: Launch New Browser

```mermaid
flowchart LR
    subgraph Script["extract_cookies.py"]
        LAUNCH["launch_persistent_context"]
        BROWSE["New Chrome Instance"]
        EXTRACT["Extract cookies"]
    end
    
    LAUNCH -->|System Chrome| BROWSE
    BROWSE --> EXTRACT
```

---

## 3. Complete Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Chrome
    participant Playwright
    participant Script
    participant JSON
    participant Scrapy
    
    User->>Chrome: Open quotes.toscrape.com/login
    User->>Chrome: Enter admin/admin
    Chrome->>Chrome: Set sessionid cookie
    
    Note over User,Chrome: Step 1: Manual Login
    
    Script->>Playwright: sync_playwright()
    Playwright->>Chrome: Connect via CDP :9222
    Chrome-->>Playwright: Connection established
    
    Note over Playwright,Chrome: Step 2: Connect
    
    Playwright->>Chrome: context.cookies()
    Chrome-->>Playwright: [sessionid, csrftoken, ...]
    
    Note over Playwright,Chrome: Step 3: Extract
    
    Playwright->>Script: all_cookies
    Script->>JSON: json.dump(cookies)
    
    Note over Script,JSON: Step 4: Save
    
    JSON->>Scrapy: Load cookies.json
    Scrapy->>Chrome: GET / with Cookie header
    
    Note over Scrapy,Chrome: Step 5: Use in Scrapy
```

---

## 4. Cookie Structure

```json
[
  {
    "name": "sessionid",
    "value": "abc123xyz789...",
    "domain": ".quotes.toscrape.com",
    "path": "/",
    "expires": 1739999999,
    "httpOnly": true,
    "secure": false,
    "sameSite": "Lax"
  },
  {
    "name": "csrftoken",
    "value": "def456abc789...",
    "domain": ".quotes.toscrape.com",
    "path": "/",
    "expires": 1739999999,
    "httpOnly": false,
    "secure": false,
    "sameSite": "Lax"
  }
]
```

---

## 5. Code Flow Diagram

```mermaid
flowchart TD
    START([Start]) --> INIT[Initialize Playwright]
    
    INIT --> TRY{"Try Connect<br/>to CDP :9222?"}
    
    TRY -->|Yes| EXISTING[Use Existing Browser]
    TRY -->|No| NEW[Launch New Chrome]
    
    EXISTING --> COOKIES[Extract Cookies]
    NEW --> COOKIES
    
    COOKIES --> SAVE[Save to cookies.json]
    SAVE --> PRINT[Print Summary]
    PRINT --> CLOSE[Close Browser]
    CLOSE --> END([End])
```

---

## 6. How Scrapy Uses the Cookies

```mermaid
flowchart LR
    subgraph Spider["quotes_spider.py"]
        LOAD[Load cookies.json]
        REQUEST[Make Request]
    end
    
    subgraph HTTP["HTTP Request"]
        HEADER[Cookie: sessionid=abc123...]
    end
    
    subgraph Server["quotes.toscrape.com"]
        VALIDATE[Validate Session]
        RESPOND[Return Protected Content]
    end
    
    LOAD --> REQUEST
    REQUEST -->|With Cookie Header| HEADER
    HEADER --> VALIDATE
    VALIDATE -->|Session Valid| RESPOND
```

---

## 7. Key Functions Explained

| Function | Purpose | Returns |
|----------|---------|---------|
| `sync_playwright()` | Creates Playwright context manager | Playwright instance |
| `connect_over_cdp()` | Connects to running Chrome | Browser instance |
| `launch_persistent_context()` | Launches new Chrome | Context instance |
| `context.cookies()` | Gets all browser cookies | List of cookies |
| `context.close()` | Cleanly closes browser | - |

---

## 8. Pros and Cons

```mermaid
flowchart LR
    subgraph PROS["✅ Advantages"]
        P1[Human handles login/captcha]
        P2[Works with any auth flow]
        P3[Simple to understand]
        P4[No reverse engineering]
    end
    
    subgraph CONS["⚠️ Limitations"]
        C1[Manual step required]
        C2[Cookie expiration]
        C3[Session timeout]
    end
    
    PROS --> Better
    CONS --> Consideration
```

---

## 9. Step-by-Step Usage

```mermaid
flowchart TD
    A[1. Open Chrome Browser] --> B[2. Go to quotes.toscrape.com/login]
    B --> C[3. Login with admin/admin]
    C --> D[4. Keep browser open]
    D --> E[5. Run: python3 extract_cookies.py]
    E --> F[6. Cookies saved to cookies.json]
    F --> G[7. Run: scrapy runspider quotes_spider.py]
    G --> H[8. Scraped data saved to quotes.json]
```

---

## 10. File Structure

```
python-scrape/
├── extract_cookies.py      # Cookie extraction script
├── quotes_spider.py        # Scrapy spider
├── quotes/
│   └── settings.py         # Scrapy configuration
├── cookies.json            # Generated cookies (output)
├── quotes.json             # Scraped data (output)
├── README.md               # This documentation
└── requirements.txt        # Python dependencies
```

---

## 11. Error Handling Flow

```mermaid
flowchart TD
    START[Try to Connect] --> SUCCESS{"Connection<br/>Successful?"}
    
    SUCCESS -->|Yes| USE[Use Existing Browser]
    SUCCESS -->|No| LAUNCH[Launch New Chrome]
    
    USE --> EXTRACT[Extract Cookies]
    LAUNCH --> EXTRACT
    
    EXTRACT --> EMPTY{"Cookies<br/>Found?"}
    
    EMPTY -->|Yes| SAVE[Save cookies.json]
    EMPTY -->|No| WARN[Print Warning]
    
    WARN --> INSTRUCT[Instructions to User]
    INSTRUCT --> END
    
    SAVE --> SUMMARY[Print Summary]
    SUMMARY --> END
```

---

## 12. Security Considerations

```mermaid
flowchart TD
    subgraph Security["Cookie Security"]
        A[✓ httpOnly flag] --> B[Prevents XSS theft]
        C[✓ Secure flag] --> D[HTTPS only transfer]
        E[✓ SameSite] --> F[CSRF protection]
    end
    
    subgraph Best_Practices["Best Practices"]
        G[Store outside git]
        H[Set short expiration]
        I[Use dedicated test accounts]
    end
```

---

## 13. Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused :9222 | Install Chrome/Chromium |
| No cookies found | Login first in browser |
| Session expired | Re-login and re-extract |
| Wrong domain cookies | Navigate to correct site first |

---

## 14. Next Steps

1. ✅ Understand the workflow
2. 📋 Try the extraction script
3. 🔧 Customize for your target site
4. 🚀 Scale to production scraping

---

*Generated for Web Scraping Learning*  
*Location: /home/richard/shared/jianglei/openclaw/python-scrape/*
