
# Reask Map API

## Introduction

The Reask Map API currently data for two products:

1. DeepCyc: high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under the current as well as future climate scenarios.  
2. HindCyc: high-resolution probabilistic tropical cyclone gust footprints both for historical storms and immediately after landfall.

The Reask Map API base URL is: `https://api.reask.earth`

Further information can be found on our website (https://reask.earth). 

## API Authentication

## DeepCyc Usage

The DeepCyc API has two endpoints:

1. `/deepcyc/v1/pointep/`: returns TC surface windspeeds at a requested latitude, longitude point and return period (inverse of the exceedance probability). The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period.

2. `/deepcyc/v1/gateep/`: returns TC surface windspeeds crossing/entering a gate at a specified return period. The gate can be a single line or a more complex shape such as a circle or square. The values returned are 1-minute averaged with no terrain correction. 




