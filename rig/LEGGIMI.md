# Aphelios: il rig

Tutto quello che serve per lavorarci in Rive (o in qualunque altro programma) sta qui.

## Pezzi del personaggio: `pezzi-base/`
Ricavati dal disegno APPROVATO: la cella centrale della griglia `out/griglia/02-vettori-a.jpg`
(dal 13/09 sera; prima venivano da 05-base.jpg, che aveva il corpo diverso). Ingrandimento 9,5x
con bordi netti, nessun ritocco. Proporzioni esatte del disegno. PNG con trasparenza. `geometria.json` dice dove sta ogni pezzo nel
quadro originale 1024x1024 (x, y, larghezza, altezza).

| pezzo | perno consigliato |
|---|---|
| `testa.png` | mento, centro (`meta.CX`, `meta.chin` in geometria.json): la testa ruota e si sporge da qui |
| `busto.png` | centro in alto. Sale 20 px sopra il collo seguendo le guance: e' il collo che si vede quando la testa si alza o ruota |
| `braccio-sx.png`, `braccio-dx.png` | spalla: `px`,`py` in geometria.json. Stanno DIETRO il busto. In cima hanno una palla (raggio 0,47 della larghezza) che il busto copre con un disco un po' piu' grande: la spalla resta tonda in ogni rotazione |
| `gamba-sx.png`, `gamba-dx.png` | in alto al centro |
| `occhio-neutro-sx.png`, `-dx.png` | centro: sono ESATTAMENTE i buchi del disegno |

Gli occhi vanno messi DENTRO una maschera a forma di testa: cosi' quando crescono non
escono mai dal nero. Nella pagina e' fatto con `mask-image`, in Rive con un clipping.

Ordine dei livelli: gambe, braccia, busto, testa, occhi (dentro la maschera testa).
I pezzi si rigenerano con `python rig/taglia-pezzi.py`: misura da solo collo, solchi delle braccia e incavo delle gambe riga per riga, e stampa quanti pixel differiscono dal disegno a riposo (solo antialias dei bordi degli occhi).

## Espressioni degli occhi: `pezzi/occhio-*.png`
tondi, arrabbiato, cuori, spirali, contento, dorme, diffidente, triste (sinistro e destro
separati). Bianchi su trasparente. Si normalizzano alla larghezza dell'occhio base x1,05.

## Oggetti: `oggetti/`
laptop, cuffie, tazza, controller, microfono, note, fumetto, cuscino, stella, cuore,
zeta, punto interrogativo. Neri su trasparente, dal foglio `out/kit/kit-oggetti-a.png`.

## Kit alternativo di Gemini: `pezzi/`
cranio senza orecchie, orecchie separate, busto, arti. Utile in Rive se si vogliono le
orecchie che si muovono da sole (nel disegno base sono fuse alla testa).

## La prospettiva (come e' fatta nella pagina)
Gli occhi stanno su una sfera di raggio = meta' larghezza testa, a +-27 gradi.
Con lo yaw `th` (da -0,62 a +0,62 rad):
- posizione x = centro + R * sin(phi + th)
- l'occhio vicino cresce fino a x1,5, quello lontano rimpicciolisce e scende di 44 px
- la testa trasla di R*sin(th)*0,28 e si stringe del 9% per lato
E' la "sbircia" che Whyed ha approvato il 12/09.

## Il cervello: `AphiBrain` in `pagina-rig.html`
Scelta stocastica (softmax a temperatura) fra: sguardo, stiracchiata, wow, sbircia,
triste, mazza, ciao, pisolino, musica, caffe', pensa, gioca, amore, niente.
I pesi dipendono da: secondi di inattivita', energia, umore (curioso/giocoso/pigro),
ora del giorno, ultima azione (che viene penalizzata per non ripetersi).
`AphiBrain.decide(ctx)` e' il gancio: un LLM (Groq o Gemini) deve restituire una di
quelle chiavi. `AphiBrain.say("testo")` mostra il fumetto.

## Come si ricostruisce la pagina
`python rig/costruisci-rig.py` prende `rig/pagina-rig.html` e `rig/pagina-stanza.html`, ci mette dentro `rig/aphi-core.js` (segnaposto `__CORE__`) con i PNG (a 32 livelli) e scrive
`demo/mascotte-rig.html`. Artifact: https://claude.ai/code/artifact/6b3e3546-1741-487d-9f69-fabb8b69419f

## Le pose disegnate: `pose/` (dal 14/09)
Le pose grandi NON sono il rig: sono le celle dei fogli approvati (`out/griglia/02-vettori-a.jpg`,
`04-vettori-quotidiano-a.jpg`, `05-camminata-a.png`) prese intere, con gli occhi come pezzi separati
(`<nome>-occhio-N.png`, i due piu' grandi sbattono e crescono). Si rigenerano con `python rig/taglia-pose.py`.
In pagina: `showPose(nome)`, cicli con `cycle([...],fps)`; `play()` torna sempre al rig.
Il rig a mesh (`mesh/`, `costruisci-mesh.py`) serve solo per la base: respiro, sguardo, occhi.

## La stanza: `pagina-stanza.html`
Artifact: https://claude.ai/code/artifact/9f4cb24c-dc41-4639-ab18-32e0b72326e1
`window.Aphi` (play, free, say, state, setDir), `window.AphiChat(testo)` da sostituire con Groq/Gemini,
`window.AphiHit(e)` per capire se il tocco e' sul personaggio.
