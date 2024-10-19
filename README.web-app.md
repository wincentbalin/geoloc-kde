# Geolocation web app

This web app in the directory `web` allows to query location from the input text without running `geoloc` utility. To achieve that, it uses web technologies and predicts location using Naive Bayes classifier (more in the [original publication](https://dl.acm.org/doi/10.5555/2887007.2887028)). It also visualises results using [Leaflet.js](https://leafletjs.com/) library.


## Model conversion

The original `geoloc` utility processes the whole model upon each run and hence does not scale well. To amend that problem in the web app, the model has to be converted into appropriate format.
In this case this format is a directory with the file `model.json`, which contains several parameters and matrices, and the subdirectory `words`, which contains word-named JSON files (for example `hello.json`, `world.json`). These word-named files contain matrices needed by the Naive Bayes classifier.

To convert the model file `model72.gz` to directory `model72/`, just run

```shell
./model2json.py model72.gz model72
```

This utility is located in the same directory as this README. It requires Python 3 to run. With other parameters you can put additional information into resulting JSON files.

## App setup

Put three files into the app directory:

- `app.html`
- `geoloc.css`
- `geoloc.js`

> Rename the file `app.html` to `index.html` if needed.

Put the model directory you created in the previous section into the app directory.

> Change the model path in the file `app.html` from `model72/` if needed. Do not forget the trailing slash, or the model will not load!

The app is ready.

## API

The geolocation algorithm was ported from C (in the file `geoloc.c`) to Javascript (in the file `geoloc.js`).

The algorithm was put into the object `GeoLoc`. After instantiating the object, load the model using the function `loadModel` and plot either a point using function `locateAsPoint` or a grid using function `locateAsGrid`, like this:

```javascript
var text = 'Testing the waters...';
var gl = new GeoLoc();
gl.loadModel('model72/');
var point = gl.locateAsPoint(text, true);
var grid = gl.locateAsGrid(text);
```

Both `locateAs...` functions use [Leaflet.js](https://leafletjs.com/) library to instantly plot the requested representation, either a point marker or a colour grid.

The Naive Bayes classifier is implemented in the function `classifyNaiveBayes`. Splitting text into words is implemented in the function `prepareWords`.