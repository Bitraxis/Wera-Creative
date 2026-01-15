WebAssembly.instantiateStreaming(fetch("main.wasm")).then((obj) => {
    console.log(obj.instance.exports.add(1, 2)); // "3"
});