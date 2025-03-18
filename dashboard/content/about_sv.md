Generation Toolkit initierades 2024 i ett pilotprojekt av [Region Västra Götaland](https://www.vgregion.se/) och [AI Sweden](https://ai.se). Målet för projektet är att sprida och fördjupa förståelsen av möjligheterna för regional självförsörjning av el.

## Vem kan använda Generation Toolkit

Generation Toolkit kan användas av regionala och lokala intressenter med intresse eller ansvar för el, samt av industrin och allmänheten. Det visuella gränssnittet är utformat för att vara lättillgängligt för alla som har en grundläggande förståelse för elproduktion.

För mer tekniskt lagda användare kan den underliggande kraftmodellen och scenariogeneratorn modifieras. Detta gör det möjligt att anpassa modellen och genomföra scenarier som återspeglar de specifika förhållandena på olika platser, vilket möjliggör djupgående analyser och skräddarsydda insikter.

**Användargrupper:**
1. Beslutsfattare (inkl. allmänheten) som ev. inte har speciella detaljkunskaper inom elområdet
2. Energispecialister som har djupare kunskap om vårt elsystem men ev. inte detaljkunskaper inom optimering och analys av kraftsystem
3. Energimodellerare som är experter på att modellera kraftsystem

## Vad är Generation Toolkit?

Generation Toolkit består av fyra komponenter som kan användas delvis oberoende av varandra.

### Komponent 1: Ett ramverk för kraftsystemsoptimering och analys

Vi har byggt en modell för lokal produktion och lagring av el från en rad energislag. Denna modell ligger till grund för resten av systemet. Vi använder [PyPSA](https://pypsa.org/) i den här komponenten, ett kraftfullt verktyg för att simulera och optimera kraftsystem.

**_Hur kan den här komponenten användas_**
- Beslutsfattare använder den här komponenten enkom genom de andra komponenterna
- Energispecialister använder den här komponenten enkom genom de andra komponenterna
- Energimodellerare kan ändra kraftsystemsmodellen, lägga till eller dra ifrån energislag eller former av lagring, samt lägga ytterliga villkor på systemet. Dessa ändringar kan sedan köras individuellt eller genom datageneratorn.

### Komponent 2: En datagenerator

Datageneratorn används för att köra ett stort antal scenarior genom vår modell. Vi kan förgenerera den data som analyseras i senare steg på ett effektivt sätt. Produktionsmodellen kan också delvis styras genom att ändra parametrarna för scenarior.

**_Hur kan den här komponenten användas_**
- Beslutsfattare använder den här komponenten enkom genom de andra komponenterna.
- Energispecialister kan ändra parametrarna i scenarior för att anpassa dem bättre till lokala villkor eller titta på specifika och särskilt relevanta scenarior.
- Energimodellerare kan köra nya modeller genom datageneratorn samt redigera indata till modellerna i likhet med energispecialisterna.

 ### Komponent 3: En API

Utdata från generatorn lagras i en API. Det gör datan tillgänglig för analys i valfri programvara och med valfria metoder.

**_Hur kan den här komponenten användas_**
- Beslutsfattare använder den här komponenten enkom genom de andra komponenterna.
- Energispecialister kan ändra parametrarna i scenarior för att anpassa dem bättre till lokala villkor eller titta på specifika och särskilt relevanta scenarior.
- Energimodellerare kan köra nya modeller genom datageneratorn samt redigera indata till modellerna i likhet med energispecialisterna.

 ### Komponent 4: En app 

För att visualisera resultaten har vi byggt en egen Streamlit-baserad app. Genom denna app ger vi alla användargrupper ett intuitivt gränssnitt för att utforska och experimentera med modellen.

**_Hur kan den här komponenten användas_**
- Beslutsfattare kan använda appen för att fördjupa sin förståelse, som underlag för möten med experter och intressenter, eller i dialog med allmänheten.
- Energispecialister kan använda appen för att lättare kommunicera i sin verksamhet.
- Energimodellerare kan använda appen för att validera och testa nya modeller.

## Kommentar gällande havsvind och 

I den nuvarande VGR-instansen av Generation Toolkit så är ingår inte havsvind eller vätgas i något scenarioresultat. Detta beror på att givet nuvarande kostnadsantagenden så krävs input från politiska beslut (andel av vind dedikerad till havsvind, samt satsningar på vätgaslagring) i modellen för att havsvind eller vätgaslagring skall inkluderas. I framtiden så kan sådan input inluderas, eller så skäl finnas att se över kostnadsantaganden på ett sådant sätt att resultatet ändras.