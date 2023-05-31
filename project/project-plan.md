# Project Plan

## Summary

Weather severly influences driving conditions. But is that influence noticable in speeding offenses, too? This project aims to discover correlations between weather conditions and speeding offenses by analyzing data provided by the city of cologne.

## Rationale

Bringing possible motivators for speeding to light helps fight these offenses.

## Datasources

<!-- Describe each datasources you plan to use in a section. Use the prefic "DatasourceX" where X is the id of the datasource. -->

### Datasource1: Speeding offsenses in Köln
* Metadata URL: https://mobilithek.info/offers/-8862870771136450928
* Data URL: https://offenedaten-koeln.de/sites/default/files/Geschwindigkeit%C3%BCberwachung_Koeln_Gesamt_2017-2021.csv
* Data Type: CSV

A CSV data set on all speeding offenses in Köln since 2017.

### Datasource2: Meteostat weather dumps
* Metadata URL: https://dev.meteostat.net/bulk/
* Data URL: https://bulk.meteostat.net/v2/hourly/10637.csv.gz
* Data Type: CSV

Data dumps of individual weather stations.

## Work Packages

<!-- List of work packages ordered sequentially, each pointing to an issue with more details. -->

- [x] [Find usable open data sources](https://github.com/derwehr/2023-saki/issues/1)
- [x] [Build data pipelines](https://github.com/derwehr/2023-saki/issues/2)
  - [x] [add data pipeline for speeding offenses & transform data](https://github.com/derwehr/2023-saki/issues/7)
  - [x] [get offense locations using the provided lookup tables](https://github.com/derwehr/2023-saki/issues/8)
  - [x] [Get geocodes for offense addresses](https://github.com/derwehr/2023-saki/issues/11)
  - [x] [add data pipeline to get weather data of the offense locations at the offense time](https://github.com/derwehr/2023-saki/issues/9)
- [x] [Analyze data and identify correlations](https://github.com/derwehr/2023-saki/issues/3)
- [ ] [Implement automated testing](https://github.com/derwehr/2023-saki/issues/4)
- [ ] [Add continous integration](https://github.com/derwehr/2023-saki/issues/5)
- [ ] [Deploy project to GH pages](https://github.com/derwehr/2023-saki/issues/6)
