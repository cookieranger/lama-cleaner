import React, { useState } from 'react'
import { useRecoilState } from 'recoil'
import { Coffee } from 'react-feather'
import { settingState } from '../../store/Atoms'
import Button from '../shared/Button'
import Modal from '../shared/Modal'

const CoffeeIcon = () => {
  const [show, setShow] = useState(false)
  const onClick = () => {
    setShow(true)
  }

  return (
    <div>
      <Button
        onClick={onClick}
        toolTip="Buy me a coffee"
        tooltipPosition="bottom"
        style={{ border: 0 }}
        icon={<Coffee />}
      />
      <Modal
        onClose={() => setShow(false)}
        title="Buy Me a Coffee"
        className="modal-setting"
        show={show}
        showCloseIcon={false}
      >
        <h4 style={{ lineHeight: '24px' }}>
          Hi there, If you found my project is useful, and want to help keep it
          alive please consider donating! Thank you for your support!
        </h4>
        <div
          style={{
            display: 'flex',
            width: '100%',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <Button onClick={() => setShow(false)}> No thanks </Button>
          <Button border onClick={() => setShow(false)}>
            <a
              href="https://ko-fi.com/Z8Z1CZJGY"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              Sure <Coffee />
            </a>
          </Button>
        </div>
      </Modal>
    </div>
  )
}

export default CoffeeIcon
