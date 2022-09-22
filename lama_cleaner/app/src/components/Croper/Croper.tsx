import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/outline'
import React, { useEffect, useState } from 'react'
import { useRecoilState, useRecoilValue } from 'recoil'
import {
  croperHeight,
  croperWidth,
  croperX,
  croperY,
  isInpaintingState,
} from '../../store/Atoms'

const DOC_MOVE_OPTS = { capture: true, passive: false }

const DRAG_HANDLE_BORDER = 2
const DRAG_HANDLE_SHORT = 12
const DRAG_HANDLE_LONG = 40

interface EVData {
  initX: number
  initY: number
  initHeight: number
  initWidth: number
  startResizeX: number
  startResizeY: number
  ord: string // top/right/bottom/left
}

interface Props {
  maxHeight: number
  maxWidth: number
  scale: number
  minHeight: number
  minWidth: number
}

const Croper = (props: Props) => {
  const { minHeight, minWidth, maxHeight, maxWidth, scale } = props
  const [x, setX] = useRecoilState(croperX)
  const [y, setY] = useRecoilState(croperY)
  const [height, setHeight] = useRecoilState(croperHeight)
  const [width, setWidth] = useRecoilState(croperWidth)
  const isInpainting = useRecoilValue(isInpaintingState)

  const [isResizing, setIsResizing] = useState(false)
  const [isMoving, setIsMoving] = useState(false)

  useEffect(() => {
    setX(Math.round((maxWidth - 512) / 2))
    setY(Math.round((maxHeight - 512) / 2))
  }, [maxHeight, maxWidth, minHeight, minWidth])

  const [evData, setEVData] = useState<EVData>({
    initX: 0,
    initY: 0,
    initHeight: 0,
    initWidth: 0,
    startResizeX: 0,
    startResizeY: 0,
    ord: 'top',
  })

  const onDragFocus = () => {
    console.log('focus')
  }

  const checkTopBottomLimit = (newY: number, newHeight: number) => {
    if (newY > 0 && newHeight > minHeight && newY + newHeight <= maxHeight) {
      return true
    }
    return false
  }

  const checkLeftRightLimit = (newX: number, newWidth: number) => {
    if (newX > 0 && newWidth > minWidth && newX + newWidth <= maxWidth) {
      return true
    }
    return false
  }

  const onPointerMove = (e: PointerEvent) => {
    if (isInpainting) {
      return
    }
    const curX = e.clientX
    const curY = e.clientY

    const offsetY = Math.round((curY - evData.startResizeY) / scale)
    const offsetX = Math.round((curX - evData.startResizeX) / scale)

    const moveTop = () => {
      const newHeight = evData.initHeight - offsetY
      const newY = evData.initY + offsetY
      if (checkTopBottomLimit(newY, newHeight)) {
        setHeight(newHeight)
        setY(newY)
      }
    }

    const moveBottom = () => {
      const newHeight = evData.initHeight + offsetY
      if (checkTopBottomLimit(evData.initY, newHeight)) {
        setHeight(newHeight)
      }
    }

    const moveLeft = () => {
      const newWidth = evData.initWidth - offsetX
      const newX = evData.initX + offsetX
      if (checkLeftRightLimit(newX, newWidth)) {
        setWidth(newWidth)
        setX(newX)
      }
    }

    const moveRight = () => {
      const newWidth = evData.initWidth + offsetX
      if (checkLeftRightLimit(evData.initX, newWidth)) {
        setWidth(newWidth)
      }
    }

    if (isResizing) {
      switch (evData.ord) {
        case 'topleft': {
          moveTop()
          moveLeft()
          break
        }
        case 'topright': {
          moveTop()
          moveRight()
          break
        }
        case 'bottomleft': {
          moveBottom()
          moveLeft()
          break
        }
        case 'bottomright': {
          moveBottom()
          moveRight()
          break
        }
        case 'top': {
          moveTop()
          break
        }
        case 'right': {
          moveRight()
          break
        }
        case 'bottom': {
          moveBottom()
          break
        }
        case 'left': {
          moveLeft()
          break
        }

        default:
          break
      }
    }

    if (isMoving) {
      const newX = evData.initX + offsetX
      const newY = evData.initY + offsetY
      if (
        checkLeftRightLimit(newX, evData.initWidth) &&
        checkTopBottomLimit(newY, evData.initHeight)
      ) {
        setX(newX)
        setY(newY)
      }
    }
  }

  const onPointerDone = (e: PointerEvent) => {
    if (isResizing) {
      setIsResizing(false)
    }

    if (isMoving) {
      setIsMoving(false)
    }
  }

  useEffect(() => {
    if (isResizing || isMoving) {
      document.addEventListener('pointermove', onPointerMove, DOC_MOVE_OPTS)
      document.addEventListener('pointerup', onPointerDone, DOC_MOVE_OPTS)
      document.addEventListener('pointercancel', onPointerDone, DOC_MOVE_OPTS)
      return () => {
        document.removeEventListener(
          'pointermove',
          onPointerMove,
          DOC_MOVE_OPTS
        )
        document.removeEventListener('pointerup', onPointerDone, DOC_MOVE_OPTS)
        document.removeEventListener(
          'pointercancel',
          onPointerDone,
          DOC_MOVE_OPTS
        )
      }
    }
  }, [isResizing, isMoving, width, height, evData])

  const onCropPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const { ord } = (e.target as HTMLElement).dataset
    if (ord) {
      setIsResizing(true)
      setEVData({
        initX: x,
        initY: y,
        initHeight: height,
        initWidth: width,
        startResizeX: e.clientX,
        startResizeY: e.clientY,
        ord,
      })
    }
  }

  const createCropSelection = () => {
    return (
      <div
        className="drag-elements"
        onFocus={onDragFocus}
        onPointerDown={onCropPointerDown}
      >
        <div
          className="drag-bar ord-top"
          data-ord="top"
          style={{ transform: `scale(${1 / scale})` }}
        />
        <div
          className="drag-bar ord-right"
          data-ord="right"
          style={{ transform: `scale(${1 / scale})` }}
        />
        <div
          className="drag-bar ord-bottom"
          data-ord="bottom"
          style={{ transform: `scale(${1 / scale})` }}
        />
        <div
          className="drag-bar ord-left"
          data-ord="left"
          style={{ transform: `scale(${1 / scale})` }}
        />

        <div
          className="drag-handle ord-topleft"
          data-ord="topleft"
          aria-label="topleft"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />

        <div
          className="drag-handle ord-topright"
          data-ord="topright"
          aria-label="topright"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />

        <div
          className="drag-handle ord-bottomleft"
          data-ord="bottomleft"
          aria-label="bottomleft"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />

        <div
          className="drag-handle ord-bottomright"
          data-ord="bottomright"
          aria-label="bottomright"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />

        <div
          className="drag-handle ord-top"
          data-ord="top"
          aria-label="top"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />
        <div
          className="drag-handle ord-right"
          data-ord="right"
          aria-label="right"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />
        <div
          className="drag-handle ord-bottom"
          data-ord="bottom"
          aria-label="bottom"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />
        <div
          className="drag-handle ord-left"
          data-ord="left"
          aria-label="left"
          tabIndex={0}
          role="button"
          style={{ transform: `scale(${1 / scale})` }}
        />
      </div>
    )
  }

  const onInfoBarPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    setIsMoving(true)
    setEVData({
      initX: x,
      initY: y,
      initHeight: height,
      initWidth: width,
      startResizeX: e.clientX,
      startResizeY: e.clientY,
      ord: '',
    })
  }

  const createInfoBar = () => {
    return (
      <div
        className="info-bar"
        onPointerDown={onInfoBarPointerDown}
        style={{
          transform: `scale(${1 / scale})`,
          top: `${10 / scale}px`,
          left: `${10 / scale}px`,
        }}
      >
        <div className="crop-size">
          {width} x {height}
        </div>
      </div>
    )
  }

  const createBorder = () => {
    return (
      <div
        className="crop-border"
        style={{
          height,
          width,
          outlineWidth: `${DRAG_HANDLE_BORDER / scale}px`,
        }}
      />
    )
  }

  return (
    <div className="croper-wrapper">
      <div className="croper" style={{ height, width, left: x, top: y }}>
        {createBorder()}
        {createInfoBar()}
        {createCropSelection()}
      </div>
    </div>
  )
}

export default Croper
