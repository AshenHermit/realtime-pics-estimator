function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class Script{
    constructor(){
        this.py.$script = this
        this.$methodCallQueue = []
        this.$nextCallId = 0
        this.$methodResolversById = {}
    }
    async $callPython(method_name, ...args){
        this.$nextCallId+=1
        var callData = {
            script_id: this.$id,
            method_name: method_name,
            call_uid: this.$nextCallId,
            args: args
        }
        this.$methodCallQueue.push(callData)
        return new Promise((function(resolve, reject){
            this.$methodResolversById[""+this.$nextCallId] = resolve
        }).bind(this))
    }
    $giveMessage(message){
        data = JSON.parse(message)
        this.$giveData(data)
    }
    $giveData(data){
        if(data.calls_results){
            data.calls_results.forEach(call_result=>{
                if("call_uid" in call_result){
                    var resolver = this.$methodResolversById[""+call_result.call_uid]
                    resolver(call_result.value)
                    delete this.$methodResolversById[""+call_result.call_uid]
                }
            })
        }
        if(data.method_call_queue){
            data.method_call_queue.forEach(method_call=>{
                if("method_name" in method_call && "args" in method_call){
                    if(!Array.isArray(method_call.args)){
                        method_call.args = [method_call.args]
                    }
                    if(method_call.method_name in this){
                        this[method_call.method_name](...method_call.args)
                    }
                }
            })
        }
    }
    $takeData(){
        var methodCallQueue = Array.from(this.$methodCallQueue)
        this.$methodCallQueue = []
        var data = {"method_call_queue": methodCallQueue}
        return JSON.stringify(data)
    }
    print(...args){
        console.log(...args)
    }
}