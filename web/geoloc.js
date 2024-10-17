function GeoLoc(map) {
    this.map = map;
    this.marker = null;
    this.layer = null;
    this.model = null;
    this.modelPath = null;
    this.wordPrior = 0.01;
    this.unk = 0.0;
}

GeoLoc.prototype.yToMidLat = function(y) {
    return y * 360.0 / this.model.granularity - 90.0 + 360.0 / this.model.granularity / 2.0;
}

GeoLoc.prototype.xToMidLon = function(x) {
    return x * 360.0 / this.model.granularity - 180.0 + 360.0 / this.model.granularity / 2.0;
}

GeoLoc.prototype.cellToY = function(cell) {
    return Math.floor(cell / this.model.granularity);
}

GeoLoc.prototype.cellToX = function(cell) {
    return cell % this.model.granularity;
}

GeoLoc.prototype.sparseMatrixToMatrix = function(sparseMatrix) {
    const granularity = this.model.granularity;
    let matrix = new Array(granularity * granularity / 2);
    matrix.fill(0.0);
    sparseMatrix.forEach(element => {
        matrix[element.x + element.y * granularity] = element.value;
    });
    return matrix;
}

/*
 * Naive Bayes:
 * p(c_i) * mass(c_i, w_1)/mass(c_i)_w * ... * mass(c_i, w_n)/mass(c_i)_w
 */
GeoLoc.prototype.classifyNaiveBayes = function(data, outputMatrix) {
    const granularity = this.model.granularity;

    /* Shortcut to speed up classification: we don't consider cells that have the minimum prior.
       This, unless we want to output the whole distribution. */
    const cMin = Math.min(...this.model.tweetsmatrix);

    /* Need to get tweetmatrix in logspace */
    let totalMatrix = this.model.tweetsmatrix.map(value => Math.log(value));

    data.forEach(element => {
        let wordData = element[1];  // Word is in element[0]
        if (wordData === null) {
            return;  // Unknown word
        }

        let tmpWordMatrix = this.sparseMatrixToMatrix(wordData.matrix);

        /* Find argmax c p(c_i) * mass(c_i|w_1)/mass(c_i)_w * ...* mass(c_i|w_n)/mass(c_i)_w */
        for (var c = 0, cn = granularity * granularity / 2; c < cn; c++) {
            if (this.model.tweetsmatrix[c] === cMin && !outputMatrix) {
                continue;
            }

            var p = tmpWordMatrix[c] + this.wordPrior;
            /* p(c)_w + prior (includes UNK) */
            var cIw = Math.log(this.model.wordmatrix[c] + this.wordPrior * (this.model.wordtypes + 1.0 + this.unk));
            p = Math.log(p) - cIw;
            totalMatrix[c] += p;
        }
    });

    for (var c = 0, cn = granularity * granularity / 2, pMax = -Infinity, maxIndex = 0; c < cn; c++) {
        if (this.model.tweetsmatrix[c] === cMin && !outputMatrix) {
            continue;
        }

        if (totalMatrix[c] > pMax) {
            pMax = totalMatrix[c];
            maxIndex = c;
        }
    }

    return {
        cell: maxIndex,
        matrix: totalMatrix
    };
}

GeoLoc.prototype.matrixToConsole = function(matrix) {
    let rows = [];
    for (var y = 0, yn = this.model.granularity / 2; y < yn; y++) {
        let row = [];
        for (var x = 0, xn = this.model.granularity; x < xn; x++) {
            row.push(matrix[x + y * this.model.granularity]);
        }
        rows.push(row.join('\t'));
    }
    console.log(rows.join('\n'));
}

GeoLoc.prototype.matrixNormalizeLog = function(matrix) {
    const max = Math.max(...matrix);
    matrix = matrix.map(value => Math.exp(value - max));
    const sum = matrix.reduce((acc, value) => acc + value, 0.0);
    matrix = matrix.map(value => value / sum);
    return matrix;
}

GeoLoc.prototype.matrixNormalize0To1 = function(matrix) {
    const min = Math.min(...matrix);
    const max = Math.max(...matrix);
    const range = max - min;
    return matrix.map(value => (value - min) / range);
}

GeoLoc.prototype.matrixToGeoJSON = function(matrix) {
    const halfCell = this.xToMidLon(this.model.granularity / 2);
    let features = matrix.map((value, cell) => {
        const midLon = this.xToMidLon(this.cellToX(cell));
        const midLat = this.yToMidLat(this.cellToY(cell));
        return {
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [midLon - halfCell, midLat - halfCell],
                    [midLon - halfCell, midLat + halfCell],
                    [midLon + halfCell, midLat + halfCell],
                    [midLon + halfCell, midLat - halfCell],
                    [midLon - halfCell, midLat - halfCell]
                ]]
            },
            properties: {
                value: value
            }
        };
    });
    return {
        type: 'FeatureCollection',
        features: features
    };
}

GeoLoc.prepareWords = function(text) {
    text = text.replace('&amp;', '&');
    text = text.replace(/@[A-Za-z0-9_]{1,15}/g, ' ');  // Remove usernames
    text = text.replace(/https:\/\/t\.co\/\w+/g, ' ');  // Remove links
    text = text.replace(/#\S+\b/g, ' ');  // Remove hashtags
    text = text.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, ' ');  // Remove emojis SO:10992921
    text = text.replace(/[().,!?"¿｀！。…:;⸜⸝&%°“”土♡_～─*+<>✩、？♬—（）【】‘〜~„`=•「」\[\]/|-]+/g, ' ');  // Remove punctuation
    text = text.replace(/\d+/g, ' ');  // Remove numbers
    text = text.toLowerCase();  // Lowercase words
    const words = text.split(/\s+/);
    console.log('Words:', words);
    return words;
}

GeoLoc.noWordsFound = function(data) {
    return data.filter(entry => entry[1] !== null).length === 0;
}

GeoLoc.prototype.fetchErrorHandler = function(msg) {
    alert(msg);
}

GeoLoc.prototype.loadModel = function(path) {
    this.modelPath = path;
    fetch(this.modelPath + 'model.json')
        .then(response => {
            if (response.status === 200) {
                return response.json();
            } else {
                this.fetchErrorHandler('Could not fetch model: ' + response.statusText);
            }
        }, reason => {
            alert(reason);
        })
        .then(data => {
            this.model = data;
            this.model.wordmatrix = this.sparseMatrixToMatrix(this.model.wordmatrix);
        });
}

GeoLoc.prototype.reset = function() {
    // Remove marker if set
    if (this.marker) {
        this.marker.remove();
        this.marker = null;
    }
    // Remove grid layer if set
    if (this.layer) {
        this.layer.remove();
        this.layer = null;
    }
}

GeoLoc.prototype.loadWords = function(words, callback) {
    Promise.all(
        words.map(word => fetch(this.modelPath + 'words/' + word + '.json')
            .then(response => response.status === 200 ? response.json() : null)
            .then(data => [word, data])
            .catch(error => GeoLoc.fetchErrorHandler('Remote error: ' + error))
    )).then(data => {
        if (GeoLoc.noWordsFound(data)) {
            console.warn('No words found!');
            return;
        }
        callback(data);
    });
};

GeoLoc.prototype.locateAsPoint = function(text, useCentroids) {
    useCentroids = useCentroids || false;
    words = GeoLoc.prepareWords(text);
    if (!words || words.length === 0) {
        return;
    }

    this.loadWords(words, data => {
        let found = this.classifyNaiveBayes(data);
        let lat = null,
            lon = null;
        if (useCentroids) {
            lat = this.model.centroids[found.cell][0];
            lon = this.model.centroids[found.cell][1];
        } else {
            lat = this.yToMidLat(this.cellToY(found.cell));
            lon = this.xToMidLon(this.cellToX(found.cell));
        }
        this.marker = L.marker([lat, lon]).addTo(this.map);
    });
}

GeoLoc.prototype.getColor = function(value) {
    return value > 0.95 ? '#ff0000' :
           value > 0.8  ? '#ffa500' :
           value > 0.66 ? '#90ee90' :
           value > 0.33 ? '#ffff00' :
                          'transparent';
}

GeoLoc.prototype.locateAsGrid = function(text) {
    words = GeoLoc.prepareWords(text);
    if (!words || words.length === 0) {
        return;
    }

    this.loadWords(words, data => {
        let found = this.classifyNaiveBayes(data, true);
        let matrix = this.matrixNormalizeLog(found.matrix);
        //this.matrixToConsole(matrix);
        matrix = this.matrixNormalize0To1(matrix);
        this.layer = L.geoJSON(this.matrixToGeoJSON(matrix), {
            style: (feature) => {
                return {
                    opacity: 0,
                    fillOpacity: 0.5,
                    color: this.getColor(feature.properties.value)
                };
            }
        }).addTo(this.map);
    });
}
