# Study This Board

# GPIO STUDY

# HAL_GPIO_WritePin()
```c
HAL_GPIO_WritePin(GPIOC, GPIO_PIN_14, GPIO_PIN_RESET);    // green off (always)
```

> 함수 설명  
> GPIO_PIN_RESET 에서 ODR 을 HIGH, LOW 로 만든다. 
> GPIO_PIN_14: ((uint16_t)0x4000) 이고
> 
> PinState 가 SET 이면
> GPIOx.BSRR 주소에 ((uint16_t)0x4000) 이 값을 넣는다.
> 
> PinState 가 RESET 이면 
> GPIO14.BSRR 주소에 (uint32_t)((uint16_t)0x4000) << 16U; 이렇게 한다.   





```c
#define PERIPH_BASE           0x40000000UL /*!< Peripheral base address in the alias region                                */
#define APB1PERIPH_BASE       PERIPH_BASE
#define AHB1PERIPH_BASE       (PERIPH_BASE + 0x00020000UL)
#define GPIOC_BASE            (AHB1PERIPH_BASE + 0x0800UL)
#define GPIOC               ((GPIO_TypeDef *) GPIOC_BASE)
# pin select
#define GPIO_PIN_13                ((uint16_t)0x2000)  /* Pin 13 selected   */ // bit mask = 2^13
#define GPIO_PIN_14                ((uint16_t)0x4000)  /* Pin 14 selected   */
# aseert
 #define GPIO_PIN_MASK              0x0000FFFFU /* PIN mask for assert test */
 #define assert_param(expr) ((void)0U)
 #define IS_GPIO_PIN_ACTION(ACTION) (((ACTION) == GPIO_PIN_RESET) || ((ACTION) == GPIO_PIN_SET))
 #define IS_GPIO_PIN(PIN)           (((((uint32_t)PIN) & GPIO_PIN_MASK ) != 0x00U) && ((((uint32_t)PIN) & ~GPIO_PIN_MASK) == 0x00U))
 
```

```c
void HAL_GPIO_WritePin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin, GPIO_PinState PinState)
{
  /* Check the parameters */
  assert_param(IS_GPIO_PIN(GPIO_Pin));
  assert_param(IS_GPIO_PIN_ACTION(PinState));

  if(PinState != GPIO_PIN_RESET) // PinState == 1
  {
    GPIOx->BSRR = GPIO_Pin;  // GPIO PIN 중 C 번 포트의 13번 을 찾아서 1로 set 하라
  }
  else
  {
    GPIOx->BSRR = (uint32_t)GPIO_Pin << 16U;
  }
}
```

### BSRR: Bit Set Register Reset

(*GPIOx).BSRR = GPIO_Pin

###
```c
typedef struct
{
  __IO uint32_t MODER;    /*!< GPIO port mode register,               Address offset: 0x00      */
  __IO uint32_t OTYPER;   /*!< GPIO port output type register,        Address offset: 0x04      */
  __IO uint32_t OSPEEDR;  /*!< GPIO port output speed register,       Address offset: 0x08      */
  __IO uint32_t PUPDR;    /*!< GPIO port pull-up/pull-down register,  Address offset: 0x0C      */
  __IO uint32_t IDR;      /*!< GPIO port input data register,         Address offset: 0x10      */
  __IO uint32_t ODR;      /*!< GPIO port output data register,        Address offset: 0x14      */
  __IO uint32_t BSRR;     /*!< GPIO port bit set/reset register,      Address offset: 0x18      */
  __IO uint32_t LCKR;     /*!< GPIO port configuration lock register, Address offset: 0x1C      */
  __IO uint32_t AFR[2];   /*!< GPIO alternate function registers,     Address offset: 0x20-0x24 */
} GPIO_TypeDef;
```

* LED 를 13 번에 초록, 14번에 빨강, 공통을 3.3V 에 꽂아서 low 가 되어야 LED 가 켜진다.

먼저 LED 를 밝히려면 GPIO out 을 써야 하는데 CUBEMX 에서 원하는 pin 을 GPIO OUT 으로 설정하고 그 핀에 원하는 LED 를 꽂는다.
다음 LED HAL_GPIO_WritePin, 










## HAL_UART_Receive_IT
```c
HAL_StatusTypeDef HAL_UART_Receive_IT(UART_HandleTypeDef *huart, uint8_t *pData, uint16_t Size)
{
  /* Check that a Rx process is not already ongoing */
  if (huart->RxState == HAL_UART_STATE_READY)
  {
    if ((pData == NULL) || (Size == 0U))
    {
      return HAL_ERROR;
    }

    /* Set Reception type to Standard reception */
    huart->ReceptionType = HAL_UART_RECEPTION_STANDARD;

    return (UART_Start_Receive_IT(huart, pData, Size));
  }
  else
  {
    return HAL_BUSY;
  }
}
```
