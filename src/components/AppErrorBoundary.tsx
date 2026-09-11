import React from 'react'
import {AlertTriangle, RefreshCw} from 'lucide-react'
import './AppErrorBoundary.css'

type State={failed:boolean}

export default class AppErrorBoundary extends React.Component<React.PropsWithChildren,State>{
  state:State={failed:false}
  static getDerivedStateFromError():State{return {failed:true}}
  componentDidCatch(error:Error){console.error('TransivoX interface error',error.name)}
  render(){
    if(!this.state.failed)return this.props.children
    return <main className="fatal-recovery"><span><AlertTriangle/></span><h1>TransivoX needs to reload</h1><p>An unexpected interface error occurred. Your saved server data is safe.</p><button onClick={()=>location.reload()}><RefreshCw/> Reload application</button></main>
  }
}
