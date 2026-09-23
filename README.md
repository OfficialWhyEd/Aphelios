# Aphelios

**Aphelios (Aphi) is WhyEd's mascot: a fragment of a black hole that behaves like a drop of ink. This repo holds the character spec, the 2D rig and the Godot project.**

Il personaggio che rappresenta WhyEd (IP as logo): una pallina nera piena con due occhi bianchi enormi, senza
pupille. L'espressione la fa solo la forma degli occhi.

## Cosa c'è
| Parte | Cosa fa |
|---|---|
| [SPECIFICA.md](SPECIFICA.md) | tutte le regole del personaggio, in ordine di importanza |
| `rig/` | il rig 2D: mesh unica con pesi fusi, pose, oggetti, `aphi-core.js` (cervello stocastico `AphiBrain`) |
| `godot/progetto/` | il rig vero in Godot 4, esportabile per il web e provato dal telefono |
| `demo/` | pagine HTML con gli stati e le pose |
| `animazione/`, `prompt/` | metodo di animazione e prompt pronti per generare pose coerenti |
| `strumenti/` | piccoli strumenti per passare immagini dal telefono al PC |

## Il metodo
1. Schizzi in bianco e nero prima, colore e contorno per ultimi.
2. Le pose si generano con un modello di immagini, una chat nuova per ogni tentativo; mai ritocchi a mano sui pixel.
3. Mai pezzi tagliati e ruotati: il corpo è una mesh unica deformata dalle ossa, come nei giochi mobile.
4. Il cervello è stocastico, non deterministico: stimolo, stato, scelta con rumore, movimento.

## Stato
Base approvata il 12/09/2026. In corso: desktop pet stile Shimeji in Godot (cammina sulle finestre, si arrampica,
reagisce a quello che scrivi), pose a figura intera, collo del rig.

---

Parte di **[WhyEcosystem 2023-2026](https://github.com/OfficialWhyEd/WhyEcosystem-2023-2026)**: il percorso di WhyEd, producer e sound engineer che costruisce sistemi AI dirigendo gli agenti.  
Costruito da WhyEd con Claude Code
