import React from 'react'

export default function RefreshButton({ onRefresh }: { onRefresh: () => void }) {
  return (
     <button onClick={onRefresh}>
        🔄 Atualizar
      </button> 
  )
}
