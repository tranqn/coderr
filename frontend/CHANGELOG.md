# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in diesem Dokument dokumentiert.

## [1.2.1] - 2025-2-03
### Geändert
- **Verbessert:** JS Doc zu allen Funktionen hinzugefügt.
- **Verbessert:** JS Doc generiert, Zugriff über ./scripts/docs.



## [1.2.0] - 2025-1-19
### Geändert
- **Bugfix:** Fehler bei Pagination in Verbindung mit Filtern behoben.
- **Bugfix:** Bild laden von Profilen (url wurde nicht erkannt wenn es mit http began).
- **Bugfix:** Revisionen von 0 ergaben einen Fehler.


- **Verbessert:** Passwort kann nun angezeigt werden nach bedarf.
- **Verbessert:** neue Toastmessage (Hint) und responsivness verbesser.
- **Verbessert:** ToastMessage wenn ohne login auf Angebot geklickt wird.
- **Verbessert:** Style-rework Dialog von "Angebot editieren/hinzufügen".
- **Verbessert:** Style-rework Pagination-Buttons für Angebote.
- **Verbessert:** Style-rework Sortierfilter für Angebote.
- **Verbessert:** Angebotsbild hinzugefügt in der Detailansicht der Angebote.
- **Verbessert:** Angebotsbild placeholder geändert.
- **Verbessert:** Neue Variante des "BUSINESS_PROFILES_URL"- und "CUSTOMER_PROFILES_URL"-response wird ebenfalls akzeptiert (user steht hierbei nicht als eigenes Object).
- **Verbessert:** Revision Eingabefeld hat mehr Validierung.



## [1.1.0] - 2024-11-21
### Geändert
- **Bugfix:** Der Fehler beim DELETE-request von reviews wurde behoben -> 204 response ist nun möglich.
- **Bugfix:** Der Fehler beim laden der leeren Details bei "Angebot erstellen" ist gelöst
- **Bugfix:** Der Fehler wenn keine reviews existierten wurde gelöst.
- **Bugfix:** Das Profilbild wird nun auch geupdated im Header, wenn das Bild geändert wird im Profil.

- **Verbessert:** "keine Angebote gefunden"-Bild hinzugefügt (offer_list.html).
- **Verbessert:** Profile sind nun zum Teil auch auf den Profilbildern verlinkt.
- **Verbessert:** Abfrage hinzugefügt ob die Bewertung wirklich gelöscht werden soll.
- **Verbessert:** Bestellbutton wird nun disabled wenn man anbieter ist (+Userfeedback darunter)


## [1.0.0] - 2024-10-01
### Erstveröffentlichung
- Initiales Release des Coderr/-Projekts.