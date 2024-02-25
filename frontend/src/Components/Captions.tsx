import { useEffect, useRef, useState } from "react"

async function getMicrophone() {
  const userMedia = await navigator.mediaDevices.getUserMedia({
    audio: true,
  })

  console.log(MediaRecorder.isTypeSupported("audio/webm; codecs=opus"))
  const mr = new MediaRecorder(userMedia)
  return mr
}

async function openMicrophone(microphone: MediaRecorder, socket: WebSocket) {
  await microphone.start(250)

  microphone.onstart = () => {
    console.log("client: microphone opened")
    document.body.classList.add("recording")
  }

  microphone.onstop = () => {
    console.log("client: microphone closed")
    document.body.classList.remove("recording")
  }

  microphone.ondataavailable = (e) => {
    const data = e.data
    // console.log("client: sent data to websocket")
    socket.send(data)
  }
}

async function closeMicrophone(microphone: MediaRecorder) {
  microphone.stop()
}

export default function Captions() {
  const wsRef = useRef<WebSocket>()

  useEffect(() => {
    wsRef.current = new WebSocket("ws://localhost:8080/audio")
    wsRef.current.onopen = async () => {
      console.log("socket opened")
      const mic = await getMicrophone()
      await openMicrophone(mic, wsRef.current!)
    }
    wsRef.current.onmessage = (msg) => {
      console.log("got msg", msg.data)
      const msgJSON = JSON.parse(msg.data)
      switch (msgJSON.Kind) {
        case "CaptionMessage":
          const m = msgJSON.Payload
          document.getElementById(m.Lang)!.innerHTML = m.Content
          break

        default:
          break
      }
    }
  }, [])

  return (
    <div>
      <p>{wsRef.current && wsRef.current.readyState === wsRef.current?.OPEN ? "Connected" : "Not connected :("}</p>
    </div>
  )
}
