# Google Cloud Storage (GCS) bucket och Speech-to-Text API

## För bästar resultat när man transcriberar via Google cloud vill man använda: 
    -  Ladda upp ljudfiler till en Google Cloud Storage (GCS) bucket.
    -  Använda Google Cloud Speech-to-Text API för att göra text av ljudfilerna.

### Då behövs en JSON-filen och Projekt-ID.

**Vad är ett Tjänstekonto (Service Account) för nåt?**
Det är typ ett specialkonto för vårt projekt, inte kopplat till en specifik person. Scriptet använder det här kontot för att logga in på Google Cloud-tjänsterna utan att behöva någons personliga inloggningsuppgifter. Smidigt!

---

### Guide: Så här fixar du JSON-nyckeln

#### **Vad du behöver ha koll på:**
* Du behöver ha tillräckliga rättigheter i Google Cloud-projektet (t.ex. "Ägare", "Redigerare" eller åtminstone "Administratör för tjänstkonton" och rätt att dela ut roller).
* Vilket **Google Cloud-projekt** vi ska använda. Det är projektet där ljudfilerna ska ligga (i en GCS-bucket) och där kostnaden för Speech-to-Text API:et hamnar.

#### **Steg-för-steg:**

1.  **Öppna Google Cloud Console:**
    Surfa in på [https://console.cloud.google.com/](https://console.cloud.google.com/)

2.  **Välj rätt Projekt:**
    Kolla högst upp på sidan så att rätt Google Cloud-projekt är valt i rullgardinsmenyn. Det ska vara projektet vi bestämt för det här.

3.  **Gå till IAM och administration > Tjänstekonton:**
    I navigeringsmenyn till vänster (klicka på "hamburgaren" ☰ om den är gömd), gå till **IAM och administration** och välj sen **Tjänstekonton**.
    *(Direktlänk om du redan är i projektet: `https://console.cloud.google.com/iam-admin/serviceaccounts`)*

4.  **Skapa ett nytt Tjänstekonto:**
    * Klicka på knappen **"+ SKAPA TJÄNSTKONTO"** högst upp.
    * **Namn på tjänstkonto:** Skriv nåt beskrivande, typ `ljudtranskribering-script-sa`.
    * **Tjänstkonto-ID:** Fylls i automatiskt. Låt det vara.
    * **Beskrivning:** Skriv en kort rad, t.ex. "Tjänstekonto för automatiskt ljudtranskriberingsscript för GCS och Speech-to-Text API."
    * Klicka på **"SKAPA OCH FORTSÄTT"**.

5.  **Ge Tjänstkontot Rättigheter (Roller):**
    Jätteviktigt steg! Tjänstkontot måste få lov att jobba med Google Cloud Storage och Speech-to-Text API:et.
    * Under "Ge det här tjänstkontot åtkomst till projektet", klicka på rullgardinsmenyn **"Välj en roll"**.
    * Lägg till dessa roller, en i taget:
        1.  **För Google Cloud Storage (ladda upp och hantera ljudfiler):**
            * Skriv `Lagringsobjektadministratör` i filterrutan.
            * Välj rollen **"Lagringsobjektadministratör"** (`roles/storage.objectAdmin`).
            * *(Tips: Vill man vara extra petig kan man ge "Lagringsobjektskapare" och "Lagringsobjektsgranskare" specifikt på GCS-bucketen sen, men "Lagringsobjektadministratör" på projektnivå är enklare att börja med).*
        2.  **För Google Cloud Speech-to-Text API (göra själva transkriberingen):**
            * Klicka på "+ LÄGG TILL YTTERLIGARE EN ROLL".
            * Skriv `Cloud Speech API-användare` i filterrutan.
            * Välj rollen **"Cloud Speech API-användare"** (`roles/speech.user`). (Alternativt funkar "Cloud AI-tjänstagent" eller mer specifika Speech-roller som "Speech-redigerare").
    * När du lagt till rollerna, klicka på **"FORTSÄTT"**.

6.  **Ge användare åtkomst till det här tjänstkontot (Valfritt):**
    Det här steget kan du hoppa över. Klicka på **"KLART"**.

7.  **Skapa och Ladda ner JSON-nyckeln:**
    * Nu borde du vara tillbaka på listan med tjänstekonton. Leta upp kontot du nyss skapade (t.ex. `ljudtranskribering-script-sa`).
    * Klicka på **Åtgärder**-menyn (tre prickar ⋮) längst ut till höger på raden för tjänstkontot, och välj sen **"Hantera nycklar"**.
    * *(Eller klicka på tjänstkontots e-postadress för att komma till detaljsidan, och klicka sen på fliken "NYCKLAR".)*
    * Klicka på **"LÄGG TILL NYCKEL"** och välj sen **"Skapa ny nyckel"**.
    * Se till att Nyckeltyp är **"JSON"** (brukar vara standard).
    * Klicka på **"SKAPA"**.
    * En JSON-fil laddas nu ner automatiskt till din dator. Det här är tjänstkontonyckeln. **Behandla filen som ett lösenord – den är superkänslig!**

8.  **Snabbkoll: Se till att API:erna är påslagna (Viktigt!):**
    För att scriptet ska funka måste följande API:er vara aktiverade i projektet:
    * **Cloud Storage API**
    * **Cloud Speech-to-Text API**
    Så här kollar/aktiverar du dem:
    * I Google Cloud Console, gå till **API:er och tjänster > Bibliotek**.
    * Sök efter "Cloud Storage API" och se till att det är aktiverat. Om inte, aktivera det.
    * Sök efter "Cloud Speech-to-Text API" och se till att det är aktiverat. Om inte, aktivera det.

---
