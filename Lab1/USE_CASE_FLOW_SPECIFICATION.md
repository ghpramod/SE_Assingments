# PES University — Department of Computer Science & Engineering
## Lab 1: Use-Case Flow Specification
### Core Use Case: UC-03 — Redeem Digital Gift Card with Anti-Fraud Voucher Locking

---

### 1. Use Case Overview
- **Use Case ID:** UC-03
- **Use Case Name:** Redeem Digital Gift Card with Anti-Fraud Voucher Locking
- **Domain:** Retail, E-Commerce & Finance (Problem Statement #34)
- **Primary Actor:** Account Holder
- **Secondary / Supporting Actors:** Merchant Partner API, Anti-Fraud & Risk Engine
- **Brief Description:** The Account Holder selects a merchant gift card and exchanges universal wallet credits for a secure, single-use digital voucher. The transaction executes automated risk scoring, applies anti-fraud voucher locking if necessary, generates cryptographic credentials, and settles ledger balances.

---

### 2. Preconditions & Postconditions
- **Preconditions:**
  1. The Account Holder is authenticated and has an active wallet session.
  2. The Account Holder possesses a verified universal exchange credit balance greater than or equal to the selected gift card denomination.
  3. The target Merchant Partner's API gateway is operational and reachable over mutual TLS.
- **Postconditions:**
  1. The required universal exchange credits are debited from the Account Holder's wallet ledger.
  2. A tamper-evident digital gift card voucher (with QR/barcode and cryptographic SHA-256 checksum) is issued and bound to the Account Holder ID.
  3. The Merchant Partner's settlement ledger is credited with the corresponding redemption claim.
  4. An immutable transaction receipt is appended to the audit log and delivered via email/push notification.

---

### 3. Main Success Scenario (Happy Path)
1. **Account Holder** accesses the digital wallet catalog and selects the target **Merchant Partner** and desired gift card denomination ($50).
2. **System** calculates the required universal exchange credits, displays applicable merchant terms, validity period, and redemption instructions.
3. **Account Holder** reviews details and confirms the redemption request.
4. **System** validates that the Account Holder's available universal exchange balance is sufficient.
5. **System** forwards transaction telemetry (Account ID, Device ID, Geo-IP, Transaction Velocity, Amount) to the **Anti-Fraud & Risk Engine** for real-time risk assessment.
6. **Anti-Fraud & Risk Engine** evaluates the telemetry, determines a low risk score (<30), and clears the transaction for immediate issuance.
7. **System** places a temporary transactional hold on the required universal exchange credits in the user's ledger.
8. **System** transmits an authenticated issuance request to the **Merchant Partner API** via secure TLS 1.3 connection.
9. **Merchant Partner API** authorizes the transaction, reserves voucher inventory, and returns a unique voucher code payload.
10. **System** generates a cryptographic SHA-256 checksum, locks the voucher to the Account Holder ID, permanently debits the credits, updates the merchant settlement ledger, and displays the scannable QR/barcode on the user's screen.

---

### 4. Alternate Flows & Exception Handling

#### Alternate Flow 4a: Insufficient Universal Credits
- **4a1.** At Step 4, if the Account Holder's credit balance is lower than the required amount:
- **4a2.** System displays an "Insufficient Balance" prompt indicating the deficit.
- **4a3.** System suggests executing `UC-02: Convert Points to Universal Credits` from linked merchant accounts.
- **4a4.** Transaction terminates safely without debiting any balance.

#### Alternate Flow 6a: High Risk Detected — Anti-Fraud Voucher Lock Triggered
- **6a1.** At Step 6, the Anti-Fraud Engine identifies suspicious indicators (e.g., unfamiliar IP address, sudden velocity surge, new unverified device) and returns a high risk score (>=70).
- **6a2.** System executes `UC-06: Apply Anti-Fraud Voucher Lock`—the voucher is placed into a `Locked-Pending Verification` state.
- **6a3.** System prompts the Account Holder for Step-Up Multi-Factor Authentication (MFA via Authenticator App or SMS OTP).
- **6a4.** Account Holder successfully submits valid MFA token within 60 seconds.
- **6a5.** System unlocks the voucher transaction and resumes execution at **Step 7** of the Main Success Scenario.

#### Alternate Flow 6b: MFA Verification Failed or Timed Out
- **6b1.** At Step 6a4, if the Account Holder fails MFA after 3 attempts or 60 seconds expire:
- **6b2.** System immediately aborts the transaction and releases all temporary credit holds.
- **6b3.** System locks voucher generation for 15 minutes, notifies the Account Holder via security alert, and logs an anomaly flag in the fraud monitoring console.

---

### 5. Special Non-Functional Requirements & Constraints
- **Latency Constraint:** The entire end-to-end redemption pipeline (Steps 1 to 10) must execute within **250 ms** under standard network conditions.
- **Integrity Guarantee:** Zero ledger drift; atomic ACID transactions ensure credits are never deducted without confirmed voucher issuance.
- **Security:** Voucher payloads encrypted at rest using AES-256 and signed with asymmetric HMAC keys.

---
