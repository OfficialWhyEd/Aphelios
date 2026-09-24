# Aphelios

**Aphelios (Aphi) is WhyEd's mascot: a fragment of a black hole that behaves like a drop of ink. This repo holds the character spec, the 2D rig with a stochastic brain, and the Godot project playable from a phone.**

`Godot 4` · `GDScript` · `Skeleton2D` · `JavaScript` · `Python (Pillow)` · `Cloudflare Workers` · stato: **rig in corso**

Il personaggio che rappresenta WhyEd (IP as logo): una pallina nera piena con due occhi bianchi enormi, senza
pupille. L'espressione la fa solo la forma degli occhi.

## Cosa fa
- **rig in Godot**: una mesh sola, il disegno approvato, mossa da uno scheletro 2D con pesi fusi;
  niente pezzi tagliati e ruotati, niente cuciture;
- **occhi veri**: sono i buchi del disegno, seguono la testa con una prospettiva a sfera (l'occhio vicino
  cresce, quello lontano si abbassa) e cambiano forma con l'espressione;
- **stati**: idle, petting, look, wow, angry, sleep, hi, comandabili con `set_state(nome)`;
- **cervello stocastico** (`AphiBrain` in `rig/aphi-core.js`): stimolo, stato interno, scelta con rumore,
  movimento. Mai due volte uguale;
- **pagine web**: la stanza dove vive, il rig da provare, gli stati;
- **esportazione web** del progetto Godot, per provarlo dal telefono.

## Come funziona
```
disegno approvato ─► rig/costruisci-mesh.py ─► mesh + pesi ─► godot/costruisci-godot.py
                                                                      │
                                                                      ▼
                            godot/progetto: aphi.tscn + aphi.gd (Skeleton2D, stati, occhi)
                                                                      │
                                                     esportazione web ─► godot/deploy (Worker)
rig/aphi-core.js (AphiBrain) ─► pagina-rig.html, pagina-stanza.html
```

## Struttura
| Percorso | Cosa contiene |
|---|---|
| [SPECIFICA.md](SPECIFICA.md) | tutte le regole del personaggio, in ordine di importanza |
| `godot/progetto/` | il progetto Godot 4: `aphi.tscn`, `aphi.gd`, texture |
| `godot/costruisci-godot.py` | costruisce la scena Godot dalla mesh |
| `godot/deploy/` | esportazione web e Worker per pubblicarla |
| `godot/screen/` | le schermate di controllo |
| `rig/` | mesh, pesi, pose (oltre 100 immagini), oggetti, `aphi-core.js`, pagine del rig e della stanza |
| `rig/LEGGIMI.md` | i pezzi, i perni e come si monta il rig |
| `rig/rive-mcp.py` | prova di collegamento a Rive via MCP |
| `demo/mascotte-stati.html` | gli stati in una pagina |
| `animazione/METODO-OLLAMA.md` | il metodo di animazione preso da come è animata la mascotte di Ollama |
| `prompt/PROMPT-PRONTI.md` | i prompt per generare pose coerenti |
| `strumenti/` | passare immagini dal telefono al PC |
| `costruisci.py` | la prima versione, generata da geometria pura |

## Come si avvia
```
# aprire godot/progetto/project.godot con Godot 4 e premere Play
# oppure le pagine web del rig:
python -m http.server 8000      # dentro rig/, poi http://localhost:8000/pagina-rig.html
```

## Il metodo
1. Schizzi in bianco e nero prima, colore e contorno per ultimi.
2. Le pose si generano con un modello di immagini, una chat nuova per ogni tentativo; mai ritocchi a mano sui pixel.
3. Mai pezzi tagliati e ruotati: il corpo è una mesh unica deformata dalle ossa, come nei giochi mobile.
4. Il cervello è stocastico, non deterministico.

## Stato
Base approvata il 12/09/2026. Idle e petting fatti. In corso: il collo del rig, pose a figura intera, e il
desktop pet in stile Shimeji (cammina sulle finestre, si arrampica, reagisce a quello che scrivi).

## Perché è nato
Un sistema costruito con gli agenti ha bisogno di una faccia. Invece di un logo astratto, un personaggio:
riconoscibile a qualunque misura, capace di reagire, e che diventa il segno di tutto l'ecosistema.

---

Parte di **[WhyEcosystem 2023-2026](https://github.com/OfficialWhyEd/WhyEcosystem-2023-2026)**: il percorso di WhyEd, producer e sound engineer che costruisce sistemi AI dirigendo gli agenti.  
Costruito da WhyEd con Claude Code
