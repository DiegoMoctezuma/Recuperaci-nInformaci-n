# Ejemplos de búsqueda (Parte D)

Top-5 por consulta y método sobre 2,126 documentos. Puntaje: similitud coseno (count, tfidf, svd, w2v, lda) o puntaje BM25 (bm25). Las consultas pasan por el mismo `preprocesar(modo="lemma")` del corpus.

## "stock market shares fall" (esperado: business)

### count: categoría dominante del top-5: business (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1617 | business | google shares fall as staff sell shares in | 0.4969 |
| 2 | doc_1448 | business | asian quake hits european shares shares in europe | 0.4301 |
| 3 | doc_1468 | business | booming markets shed few tears the market former | 0.4103 |
| 4 | doc_1242 | business | nasdaq planning $100m share sale the owner of | 0.3599 |
| 5 | doc_1967 | business | hariri killing hits beirut shares shares in solidere | 0.3482 |

### tfidf: categoría dominante del top-5: business (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1617 | business | google shares fall as staff sell shares in | 0.3125 |
| 2 | doc_1967 | business | hariri killing hits beirut shares shares in solidere | 0.2273 |
| 3 | doc_1893 | business | bat spit drug firm goes to market a | 0.2270 |
| 4 | doc_0064 | business | india power shares jump on debut shares in | 0.2199 |
| 5 | doc_1242 | business | nasdaq planning $100m share sale the owner of | 0.2182 |

### bm25: categoría dominante del top-5: business (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1617 | business | google shares fall as staff sell shares in | 15.4562 |
| 2 | doc_1448 | business | asian quake hits european shares shares in europe | 13.1850 |
| 3 | doc_1967 | business | hariri killing hits beirut shares shares in solidere | 13.1175 |
| 4 | doc_0913 | business | irish markets reach all-time high irish shares have | 12.7383 |
| 5 | doc_0314 | business | takeover offer for sunderland fc bob murray chairman | 12.3850 |

### svd: categoría dominante del top-5: business (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1967 | business | hariri killing hits beirut shares shares in solidere | 0.6610 |
| 2 | doc_1617 | business | google shares fall as staff sell shares in | 0.5971 |
| 3 | doc_1893 | business | bat spit drug firm goes to market a | 0.5315 |
| 4 | doc_1242 | business | nasdaq planning $100m share sale the owner of | 0.5174 |
| 5 | doc_0913 | business | irish markets reach all-time high irish shares have | 0.5157 |

### w2v: categoría dominante del top-5: business (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1242 | business | nasdaq planning $100m share sale the owner of | 0.8217 |
| 2 | doc_0447 | business | nasdaq planning $100m-share sale the owner of the | 0.8168 |
| 3 | doc_1967 | business | hariri killing hits beirut shares shares in solidere | 0.7892 |
| 4 | doc_0913 | business | irish markets reach all-time high irish shares have | 0.7797 |
| 5 | doc_1448 | business | asian quake hits european shares shares in europe | 0.7785 |

### lda: categoría dominante del top-5: business (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1818 | business | german economy rebounds germany s economy the biggest | 0.9980 |
| 2 | doc_2018 | business | us trade deficit widens sharply the gap between | 0.9980 |
| 3 | doc_0246 | business | steady job growth continues in us the us | 0.9980 |
| 4 | doc_1352 | business | manufacturing recovery slowing uk manufacturing grew at its | 0.9978 |
| 5 | doc_0152 | business | german business confidence slides german business confidence fell | 0.9978 |

## "election labour party vote" (esperado: politics)

### count: categoría dominante del top-5: politics (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1461 | politics | kennedy s cautious optimism charles kennedy is far | 0.5381 |
| 2 | doc_1450 | politics | lib dems unveil election slogan the liberal democrats | 0.5311 |
| 3 | doc_0484 | politics | kennedy looks to election gains they may not | 0.5126 |
| 4 | doc_1208 | politics | sainsbury s labour election gift science minister lord | 0.5121 |
| 5 | doc_1498 | politics | labour faces cold calls inquiry labour is to | 0.4831 |

### tfidf: categoría dominante del top-5: politics (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_0259 | politics | ukip outspent labour on eu poll the uk | 0.3141 |
| 2 | doc_0196 | politics | lib dems predict best ever poll the lib | 0.2981 |
| 3 | doc_1450 | politics | lib dems unveil election slogan the liberal democrats | 0.2724 |
| 4 | doc_0980 | politics | parties warned over grey vote political parties cannot | 0.2706 |
| 5 | doc_1208 | politics | sainsbury s labour election gift science minister lord | 0.2655 |

### bm25: categoría dominante del top-5: politics (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1450 | politics | lib dems unveil election slogan the liberal democrats | 16.4488 |
| 2 | doc_0818 | politics | muslims discuss election concerns issues that muslims should | 16.1867 |
| 3 | doc_1358 | politics | parties warned over grey vote political parties cannot | 15.9334 |
| 4 | doc_0259 | politics | ukip outspent labour on eu poll the uk | 15.8477 |
| 5 | doc_1267 | politics | milburn defends poster campaign labour s election chief | 15.7072 |

### svd: categoría dominante del top-5: politics (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_0259 | politics | ukip outspent labour on eu poll the uk | 0.6740 |
| 2 | doc_0513 | politics | labour mp praises tory campaign the conservatives have | 0.6149 |
| 3 | doc_0375 | politics | top tories on lib dem hit list the | 0.6107 |
| 4 | doc_1208 | politics | sainsbury s labour election gift science minister lord | 0.6106 |
| 5 | doc_0818 | politics | muslims discuss election concerns issues that muslims should | 0.5918 |

### w2v: categoría dominante del top-5: politics (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_0259 | politics | ukip outspent labour on eu poll the uk | 0.8636 |
| 2 | doc_1208 | politics | sainsbury s labour election gift science minister lord | 0.8305 |
| 3 | doc_0375 | politics | top tories on lib dem hit list the | 0.8262 |
| 4 | doc_1960 | politics | kennedy begins pre-election tour liberal democrat leader charles | 0.8256 |
| 5 | doc_0484 | politics | kennedy looks to election gains they may not | 0.8242 |

### lda: categoría dominante del top-5: politics (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_0880 | politics | lib dems target the student vote students can | 0.9981 |
| 2 | doc_1860 | politics | labour seeks to quell feud talk labour s | 0.9980 |
| 3 | doc_1148 | politics | what really divides the parties so what is | 0.9980 |
| 4 | doc_1225 | politics | blair to face mps amid feud talk tony | 0.9977 |
| 5 | doc_0387 | politics | will tory tax cuts lift spirits michael howard | 0.9977 |

## "mobile phone software" (esperado: tech)

### count: categoría dominante del top-5: tech (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1946 | tech | friends fear with lost mobiles people are becoming | 0.6172 |
| 2 | doc_1692 | tech | home phones face unclear future the fixed line | 0.6106 |
| 3 | doc_0844 | tech | finding new homes for old phones re-using old | 0.5831 |
| 4 | doc_0872 | tech | mobiles rack up 20 years of use mobile | 0.5422 |
| 5 | doc_1504 | tech | moving mobile improves golf swing a mobile phone | 0.5333 |

### tfidf: categoría dominante del top-5: tech (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1692 | tech | home phones face unclear future the fixed line | 0.3014 |
| 2 | doc_1946 | tech | friends fear with lost mobiles people are becoming | 0.2710 |
| 3 | doc_0027 | tech | mobile gig aims to rock 3g forget about | 0.2648 |
| 4 | doc_0872 | tech | mobiles rack up 20 years of use mobile | 0.2544 |
| 5 | doc_1504 | tech | moving mobile improves golf swing a mobile phone | 0.2432 |

### bm25: categoría dominante del top-5: tech (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1946 | tech | friends fear with lost mobiles people are becoming | 15.0039 |
| 2 | doc_0748 | tech | hotspot users gain free net calls people using | 14.2749 |
| 3 | doc_1296 | tech | cebit opens to mobile music tune cebit the | 13.5668 |
| 4 | doc_0024 | tech | mobile audio enters new dimension as mobile phones | 13.4738 |
| 5 | doc_0782 | tech | fast moving phone viruses appear security firms are | 13.2117 |

### svd: categoría dominante del top-5: tech (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_0872 | tech | mobiles rack up 20 years of use mobile | 0.7442 |
| 2 | doc_1946 | tech | friends fear with lost mobiles people are becoming | 0.6514 |
| 3 | doc_1692 | tech | home phones face unclear future the fixed line | 0.6445 |
| 4 | doc_0923 | tech | cheaper chip for mobiles a mobile phone chip | 0.6236 |
| 5 | doc_0027 | tech | mobile gig aims to rock 3g forget about | 0.6114 |

### w2v: categoría dominante del top-5: tech (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_1692 | tech | home phones face unclear future the fixed line | 0.8395 |
| 2 | doc_1504 | tech | moving mobile improves golf swing a mobile phone | 0.8266 |
| 3 | doc_0872 | tech | mobiles rack up 20 years of use mobile | 0.8207 |
| 4 | doc_1927 | tech | half of uk s mobiles go online multimedia | 0.8139 |
| 5 | doc_0844 | tech | finding new homes for old phones re-using old | 0.8078 |

### lda: categoría dominante del top-5: tech (5/5)

| rank | doc_id | category | titulo | score |
|---|---|---|---|---|
| 1 | doc_2080 | tech | mobile tv tipped as one to watch scandinavians | 0.9969 |
| 2 | doc_0329 | tech | cebit fever takes over hanover thousands of products | 0.9965 |
| 3 | doc_0068 | tech | microsoft gets the blogging bug software giant microsoft | 0.9964 |
| 4 | doc_0630 | tech | more power to the people says hp the | 0.9963 |
| 5 | doc_0990 | tech | gadget show heralds mp3 season partners of those | 0.9963 |

## Resumen: categoría dominante del top-5

| consulta (esperado) | count | tfidf | bm25 | svd | w2v | lda |
|---|---|---|---|---|---|---|
| stock market shares fall (business) | business (5/5) | business (5/5) | business (5/5) | business (5/5) | business (5/5) | business (5/5) |
| election labour party vote (politics) | politics (5/5) | politics (5/5) | politics (5/5) | politics (5/5) | politics (5/5) | politics (5/5) |
| mobile phone software (tech) | tech (5/5) | tech (5/5) | tech (5/5) | tech (5/5) | tech (5/5) | tech (5/5) |
