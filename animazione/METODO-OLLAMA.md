# Come hanno animato la mascotte di Ollama

Fonte: post Instagram di **novra.design** con **ab.workss**, due video mandati da Whyed
l'11/09/2026 alle 05:04. Ricostruito guardando i fotogrammi.

## Le fasi, nell'ordine

**01 SKETCHES** - nove schizzi a matita (rossa) su una griglia 3x3. Sono nove POSE
diverse dello stesso personaggio: saluta, timido, arrabbiato, colpito, normale, con la
mazza, innamorato, che mangia, ecc. Sono grezzi, servono solo a fissare l'attitudine.

**02 VECTORS** - gli stessi nove schizzi ridisegnati puliti in vettoriale nero, stessa
griglia 3x3. Qui il personaggio diventa definitivo: linea uniforme, forme chiuse.

**03 RIGGING** - il personaggio viene montato con i controlli:
- un **trackpad quadrato** con un pallino: due assi X/Y, muove testa e sguardo
- **slider orizzontali** in alto: due, per le orecchie
- **slider verticali** ai lati: due, per le braccia
- uno **slider sotto**: il corpo
Ogni controllo e' un parametro che deforma il vettoriale.

**04 ANIMATION** - una **macchina a stati** con i pulsanti nominati:
`Hi` `Idle` `Dealer` `Hover on download` `Petting` `Slap L` `Slap R` `Angry`.
Ogni stato e' un'animazione, e il sito la richiama in base a cosa fa il visitatore
(fermo, passa sul tasto download, ci clicca sopra, lo accarezza...).

## Con cosa e' fatto

I controlli con slider + trackpad + macchina a stati sono il modo di lavorare di **Rive**
(rive.app): si disegna il vettoriale, si mette il rig, si costruisce la state machine e si
esporta un `.riv` che gira nel sito e reagisce al mouse. Alternativa piu' povera: Lottie
(solo animazioni fisse, niente interazione) o sprite CSS.

## Cosa vuol dire per noi

La mascotte di WhyEd e' gia' alla fine della fase 02 (vettoriale approvato).
Il prossimo passo e' **la griglia delle pose**, poi il rig, poi gli stati.
