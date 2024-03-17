# 겜린더 백엔드 로컬 환경 코드

## Blog Post
[MongoDB는 겜린더에 적합한 DB일까?](https://velog.io/@grit_munhyeok/겜린더-백엔드-문제-인식과-문제-해결을-위한-조사)

[Redis를 이용해 겜린더 검색 자동완성 성능을 개선해 보기](https://velog.io/@grit_munhyeok/겜린더-검색-자동완성-성능을-개선해-보기)

## 실제 겜린더에 사용할 용도로 제작 중입니다.

### Language
Python

### Web Framework
FastAPI

Model - Schema - Route 구조

### DB
MongoDB, Redis

### Implementation
Game CRUD
- Game Data Caching

Search
- Autocomplete (검색어 자동완성)
- MongoDB Full Text Search & Redis Search Result Caching

Notice CRUD (구현 예정)

Redis Caching
- Calendar Data
- GameInfo
- Search Result

### Caching Strategies
Look-Aside
![](/Readme%20Image/Caching%20Strategies.png)

### Architecture
![](/Readme%20Image/Back-End%20Architecture.png)

### AutoComplete Sequence Diagram
![](/Readme%20Image/Autocomplete_Diagram.png)



------

## Server H/W
- Raspberry Pi 4 (Ubuntu Server)